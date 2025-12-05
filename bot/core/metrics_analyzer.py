import re
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class PRMetrics:
    """Metrics for a PR review"""
    total_lines_added: int
    total_lines_removed: int
    total_lines_changed: int
    files_changed: int
    security_keywords_found: List[str]
    complexity_score: float  # 0-100
    estimated_review_time: str
    risk_level: str  # LOW, MEDIUM, HIGH
    
    def to_dict(self) -> Dict:
        return {
            'lines_added': self.total_lines_added,
            'lines_removed': self.total_lines_removed,
            'lines_changed': self.total_lines_changed,
            'files_changed': self.files_changed,
            'security_keywords': self.security_keywords_found,
            'complexity_score': f"{self.complexity_score:.1f}%",
            'estimated_review_time': self.estimated_review_time,
            'risk_level': self.risk_level,
        }

class MetricsAnalyzer:
    """Analyze diff and generate metrics"""
    
    SECURITY_KEYWORDS = {
        'eval(': 'critical',
        'exec(': 'critical',
        'os.system': 'high',
        '__import__': 'high',
        'pickle': 'high',
        'password': 'medium',
        'api_key': 'medium',
        'secret': 'medium',
        'TOKEN': 'medium',
        'credentials': 'medium',
    }
    
    @staticmethod
    def analyze(diff: str) -> PRMetrics:
        """Analyze diff and return metrics"""
        lines = diff.splitlines()
        added_lines = len([l for l in lines if l.startswith('+')])
        removed_lines = len([l for l in lines if l.startswith('-')])
        changed_lines = added_lines + removed_lines
        
        # Count files changed
        files_changed = len([l for l in lines if l.startswith('diff --git')])
        
        # Find security keywords
        security_found = []
        for keyword, severity in MetricsAnalyzer.SECURITY_KEYWORDS.items():
            if keyword in diff:
                security_found.append(keyword)
        
        # Calculate complexity score based on various factors
        complexity_score = MetricsAnalyzer._calculate_complexity(
            changed_lines, files_changed, len(security_found)
        )
        
        # Estimate review time
        review_time = MetricsAnalyzer._estimate_review_time(changed_lines)
        
        # Determine risk level
        risk_level = MetricsAnalyzer._assess_risk(
            complexity_score, len(security_found), files_changed
        )
        
        return PRMetrics(
            total_lines_added=added_lines,
            total_lines_removed=removed_lines,
            total_lines_changed=changed_lines,
            files_changed=files_changed,
            security_keywords_found=security_found,
            complexity_score=complexity_score,
            estimated_review_time=review_time,
            risk_level=risk_level,
        )
    
    @staticmethod
    def _calculate_complexity(lines_changed: int, files_changed: int, security_issues: int) -> float:
        """Calculate complexity score (0-100)"""
        score = 0.0
        
        # Lines changed factor (max 40 points)
        if lines_changed > 500:
            score += 40
        elif lines_changed > 200:
            score += 30
        elif lines_changed > 50:
            score += 15
        else:
            score += 5
        
        # Files changed factor (max 30 points)
        if files_changed > 10:
            score += 30
        elif files_changed > 5:
            score += 20
        elif files_changed > 2:
            score += 10
        else:
            score += 5
        
        # Security issues factor (max 30 points)
        score += min(security_issues * 10, 30)
        
        return min(score, 100)
    
    @staticmethod
    def _estimate_review_time(lines_changed: int) -> str:
        """Estimate review time based on lines changed"""
        minutes = max(5, lines_changed // 50)
        if minutes < 60:
            return f"{minutes} min"
        hours = minutes // 60
        remaining = minutes % 60
        if remaining == 0:
            return f"{hours}h"
        return f"{hours}h {remaining}min"
    
    @staticmethod
    def _assess_risk(complexity: float, security_issues: int, files_changed: int) -> str:
        """Assess risk level"""
        if complexity > 70 or security_issues > 2 or files_changed > 15:
            return "HIGH"
        elif complexity > 40 or security_issues > 0 or files_changed > 5:
            return "MEDIUM"
        return "LOW"
