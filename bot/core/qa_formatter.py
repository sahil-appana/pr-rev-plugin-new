from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class QAIssue:
    """Represents a QA issue found in code"""
    title: str
    description: str
    severity: str  # LOW, MEDIUM, HIGH
    category: str  # bug, validation, logical, security, edge_case, test_gap, refactor
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    suggested_fix: Optional[str] = None  # Diff format
    test_suggestion: Optional[str] = None

@dataclass
class QAReport:
    """Structured QA review report"""
    summary: str
    bugs_found: List[QAIssue]
    logical_issues: List[QAIssue]
    validation_gaps: List[QAIssue]
    security_issues: List[QAIssue]
    edge_cases: List[QAIssue]
    test_gaps: List[QAIssue]
    refactor_suggestions: List[QAIssue]
    final_recommendation: str
    
    def get_all_issues(self) -> List[QAIssue]:
        """Get all issues in one list"""
        return (self.bugs_found + self.logical_issues + self.validation_gaps + 
                self.security_issues + self.edge_cases + self.test_gaps + 
                self.refactor_suggestions)
    
    def get_high_severity(self) -> List[QAIssue]:
        """Get all HIGH severity issues"""
        return [issue for issue in self.get_all_issues() if issue.severity == 'HIGH']
    
    def get_medium_severity(self) -> List[QAIssue]:
        """Get all MEDIUM severity issues"""
        return [issue for issue in self.get_all_issues() if issue.severity == 'MEDIUM']

class QAFormatter:
    """Format QA review report as markdown"""
    
    @staticmethod
    def format_report(report: QAReport) -> str:
        """Format QA report as markdown comment"""
        lines = []
        
        # Header
        lines.append("## QA Testing Review Report")
        lines.append("*Comprehensive analysis performed in QA Mode*")
        lines.append("")
        
        # Summary
        lines.append("### Executive Summary")
        lines.append(report.summary)
        lines.append("")
        
        # Statistics
        all_issues = report.get_all_issues()
        high_severity = report.get_high_severity()
        medium_severity = report.get_medium_severity()
        
        lines.append("### Issues Summary")
        lines.append(f"- **Total Issues**: {len(all_issues)}")
        lines.append(f"- **HIGH Severity**: {len(high_severity)}")
        lines.append(f"- **MEDIUM Severity**: {len(medium_severity)}")
        lines.append("")
        
        # Bugs Found
        if report.bugs_found:
            lines.append("### 🐛 Bugs Detected")
            for issue in report.bugs_found:
                lines.extend(QAFormatter._format_issue(issue))
            lines.append("")
        
        # Logical Issues
        if report.logical_issues:
            lines.append("### ⚙️ Logical Issues")
            for issue in report.logical_issues:
                lines.extend(QAFormatter._format_issue(issue))
            lines.append("")
        
        # Validation Gaps
        if report.validation_gaps:
            lines.append("### ✅ Missing Validations")
            for issue in report.validation_gaps:
                lines.extend(QAFormatter._format_issue(issue))
            lines.append("")
        
        # Security Issues
        if report.security_issues:
            lines.append("### 🔒 Security Concerns")
            for issue in report.security_issues:
                lines.extend(QAFormatter._format_issue(issue))
            lines.append("")
        
        # Edge Cases
        if report.edge_cases:
            lines.append("### 🎯 Edge Cases Not Handled")
            for issue in report.edge_cases:
                lines.extend(QAFormatter._format_issue(issue))
            lines.append("")
        
        # Test Gaps
        if report.test_gaps:
            lines.append("### 🧪 Unit Test Gaps")
            for issue in report.test_gaps:
                lines.extend(QAFormatter._format_issue(issue))
            lines.append("")
        
        # Refactor Suggestions
        if report.refactor_suggestions:
            lines.append("### 🔄 Refactoring Recommendations")
            for issue in report.refactor_suggestions:
                lines.extend(QAFormatter._format_issue(issue))
            lines.append("")
        
        # Final Recommendation
        lines.append("### Final Recommendation")
        lines.append(report.final_recommendation)
        lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def _format_issue(issue: QAIssue) -> List[str]:
        """Format a single QA issue"""
        lines = []
        
        # Issue header with severity
        severity_emoji = {
            'HIGH': '🔴',
            'MEDIUM': '🟡',
            'LOW': '🟢'
        }.get(issue.severity, '⚪')
        
        lines.append(f"{severity_emoji} **{issue.title}** ({issue.severity})")
        lines.append(f"- {issue.description}")
        
        # Location if available
        if issue.file_path and issue.line_number:
            lines.append(f"- **Location**: `{issue.file_path}:{issue.line_number}`")
        
        # Suggested fix
        if issue.suggested_fix:
            lines.append("- **Suggested Fix**:")
            lines.append("```diff")
            lines.append(issue.suggested_fix)
            lines.append("```")
        
        # Test suggestion
        if issue.test_suggestion:
            lines.append("- **Test Case**:")
            lines.append("```python")
            lines.append(issue.test_suggestion)
            lines.append("```")
        
        lines.append("")
        return lines
    
    @staticmethod
    def format_inline_comment(issue: QAIssue) -> str:
        """Format issue for inline comment on specific line"""
        severity_emoji = {
            'HIGH': '🔴',
            'MEDIUM': '🟡',
            'LOW': '🟢'
        }.get(issue.severity, '⚪')
        
        comment = f"{severity_emoji} **QA Issue** ({issue.severity}): {issue.title}\n\n"
        comment += f"{issue.description}\n"
        
        if issue.suggested_fix:
            comment += f"\n**Fix**:\n```diff\n{issue.suggested_fix}\n```"
        
        return comment
