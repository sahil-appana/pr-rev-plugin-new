# Small utilities to operate on diffs.
def count_lines(diff_text: str) -> int:
    return len(diff_text.splitlines())

def has_keyword(diff_text: str, keyword: str) -> bool:
    return keyword in diff_text
