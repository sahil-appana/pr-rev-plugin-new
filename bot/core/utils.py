import re
from typing import List, Dict

def safe_preview(text: str, max_chars: int = 5000) -> str:
    """Safely preview text with truncation"""
    return text[:max_chars] + ('... (truncated)' if len(text) > max_chars else '')

def extract_file_path_from_diff_line(line: str) -> str:
    """Extract file path from diff header line"""
    # Handles: diff --git a/path/to/file b/path/to/file
    match = re.search(r'a/(.*?)\s+b/', line)
    if match:
        return match.group(1)
    return ''

def parse_diff_stats(diff: str) -> Dict[str, int]:
    """Parse diff statistics"""
    files = len(re.findall(r'^diff --git', diff, re.MULTILINE))
    additions = len(re.findall(r'^\+', diff, re.MULTILINE))
    deletions = len(re.findall(r'^-', diff, re.MULTILINE))
    return {
        'files': files,
        'additions': additions,
        'deletions': deletions,
        'total_changes': additions + deletions
    }

def find_code_patterns(diff: str, patterns: List[str]) -> Dict[str, int]:
    """Find occurrences of code patterns in diff"""
    results = {}
    for pattern in patterns:
        # Case-insensitive search
        matches = re.findall(rf'\b{re.escape(pattern)}\b', diff, re.IGNORECASE)
        if matches:
            results[pattern] = len(matches)
    return results

def is_large_diff(diff: str, threshold: int = 10000) -> bool:
    """Check if diff exceeds size threshold"""
    return len(diff) > threshold

def validate_diff(diff: str) -> bool:
    """Validate that diff has proper format"""
    if not diff:
        return False
    return 'diff --git' in diff or '+++' in diff or '---' in diff
