import re
from typing import List, Dict, Optional, Tuple
from bot.core.logger import ReviewLogger
from bot.core.qa_formatter import QAIssue

class QAIssueExtractor:
    """Extract QA issues from review text and map them to file locations"""
    
    def __init__(self):
        self.logger = ReviewLogger.get()
    
    def extract_issues(self, review_text: str) -> List[QAIssue]:
        """Extract issues from QA review text"""
        issues = []
        
        # Parse each major section
        issues.extend(self._extract_section_issues(review_text, 'Bugs Detected', 'bug'))
        issues.extend(self._extract_section_issues(review_text, 'Missing Validations', 'validation'))
        issues.extend(self._extract_section_issues(review_text, 'Logical Issues', 'logical'))
        issues.extend(self._extract_section_issues(review_text, 'Security Concerns', 'security'))
        issues.extend(self._extract_section_issues(review_text, 'Edge Cases Not Handled', 'edge_case'))
        issues.extend(self._extract_section_issues(review_text, 'Unit Test Gaps', 'test_gap'))
        issues.extend(self._extract_section_issues(review_text, 'Code Improvements', 'refactor'))
        
        return issues
    
    def _extract_section_issues(self, text: str, section_name: str, category: str) -> List[QAIssue]:
        """Extract issues from a specific section"""
        issues = []
        
        # Find section
        pattern = rf'###?\s*{re.escape(section_name)}.*?(?=###|\Z)'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        
        if not match:
            return issues
        
        section_text = match.group(0)
        
        # Extract individual issues (look for bullets or numbered items)
        issue_patterns = [
            r'(?:^|\n)(?:-|\*|\d+\.\s+)?\s*([^\n]+?)(?:\n\s*(?:-|to:|Location:|Fix:|Test:))?',
        ]
        
        for line in section_text.split('\n'):
            line = line.strip()
            
            # Skip headers and empty lines
            if not line or line.startswith('#') or line.startswith('*'):
                continue
            
            # Extract severity
            severity = 'MEDIUM'
            if 'HIGH' in line:
                severity = 'HIGH'
            elif 'LOW' in line:
                severity = 'LOW'
            
            # Extract file and line number if present
            file_path = None
            line_number = None
            location_match = re.search(r'`?([^`\s]+\.\w+):(\d+)`?', line)
            if location_match:
                file_path = location_match.group(1)
                line_number = int(location_match.group(2))
            
            # Skip if too short or looks like metadata
            if len(line) > 20 and 'No issues' not in line:
                # Remove severity and location from title
                title = re.sub(r'\((HIGH|MEDIUM|LOW)\)', '', line).strip()
                title = re.sub(r'`[^`]+:\d+`', '', title).strip()
                
                if title:
                    issue = QAIssue(
                        title=title[:100],  # Limit title
                        description=line,
                        severity=severity,
                        category=category,
                        file_path=file_path,
                        line_number=line_number
                    )
                    issues.append(issue)
        
        return issues
    
    def extract_high_medium_issues(self, issues: List[QAIssue]) -> List[QAIssue]:
        """Filter for HIGH and MEDIUM severity issues suitable for inline comments"""
        return [issue for issue in issues 
                if issue.severity in ['HIGH', 'MEDIUM'] and 
                issue.file_path and issue.line_number]
    
    def group_issues_by_location(self, issues: List[QAIssue]) -> Dict[Tuple[str, int], List[QAIssue]]:
        """Group issues by file path and line number"""
        grouped = {}
        for issue in issues:
            if issue.file_path and issue.line_number:
                key = (issue.file_path, issue.line_number)
                if key not in grouped:
                    grouped[key] = []
                grouped[key].append(issue)
        return grouped
