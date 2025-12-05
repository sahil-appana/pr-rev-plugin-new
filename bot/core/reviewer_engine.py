import json
import hashlib
from bot.core.model_router import ModelRouter
from bot.core.diff_fetcher import count_lines
from bot.core.cache_manager import CacheManager
from bot.core.metrics_analyzer import MetricsAnalyzer
from bot.core.logger import ReviewLogger
from bot.core.comment_builder import build_markdown_comment
from bot.core.qa_formatter import QAFormatter, QAReport, QAIssue
from bot.config import Config

def truncate_diff(diff, max_chars=14000):
    if len(diff) <= max_chars:
        return diff
    # keep head and tail
    head = diff[:7000]
    tail = diff[-7000:]
    return head + "\n\n...TRUNCATED...\n\n" + tail

class ReviewerEngine:
    def __init__(self):
        self.router = ModelRouter()
        self.cache = CacheManager(Config.CACHE_DIR, Config.CACHE_TTL) if Config.ENABLE_CACHING else None
        self.logger = ReviewLogger.get()
        
        rules_path = 'bot/rules/rules.json'
        try:
            with open(rules_path, 'r', encoding='utf-8') as f:
                self.rules = json.load(f)
        except Exception as e:
            self.logger.warning(f"Could not load rules from {rules_path}: {e}")
            self.rules = {}

    def _get_cache_key(self, title: str, description: str, diff: str) -> str:
        """Generate cache key for review"""
        content = f"{title}|{description}|{diff[:1000]}"  # Use first 1000 chars of diff
        return hashlib.sha256(content.encode()).hexdigest()

    def build_prompt(self, title, description, diff):
        """Build QA-focused review prompt - QA Mode ALWAYS ACTIVE"""
        truncated_diff = truncate_diff(diff, Config.MAX_DIFF_CHARS)
        
        qa_prompt = f"""You are an expert QA engineer and senior code reviewer.
Your primary job is to identify ALL potential issues in code changes and ensure quality.

For the following Pull Request, perform COMPREHENSIVE QA TESTING including:

### REQUIRED OUTPUT SECTIONS (MUST INCLUDE ALL):

1. **QA Summary** - Overall assessment of quality and risk level
2. **Bugs Detected** - Any bugs, logic errors, or incorrect implementations
3. **Missing Validations** - Input validation, null checks, boundary conditions
4. **Logical Issues** - Flawed business logic, incorrect algorithms, edge cases
5. **Security Concerns** - Vulnerabilities, unsafe patterns, credential handling
6. **Edge Cases Not Handled** - Scenarios that could fail or cause errors
7. **Unit Test Gaps** - Missing test coverage and test scenarios needed
8. **Code Improvements** - Refactoring suggestions, performance optimization
9. **Final Recommendation** - Approve/Request Changes with priority

### CRITICAL: PROVIDE CODE FIXES FOR EVERY ISSUE

For EVERY issue found, you MUST provide:
- Clear explanation of the problem
- Severity level: LOW / MEDIUM / HIGH
- Suggested fix in unified diff format (showing before/after)
- Unit test case to verify the fix

### Diff Format for Fixes:
```diff
- old_code_here
+ new_code_here
```

### Test Format for Fixes:
```python
def test_new_behavior():
    # Test the fix here
    assert condition
```

---

### PULL REQUEST DETAILS
Title: {title}
Description: {description}

### CODE CHANGES TO REVIEW
```diff
{truncated_diff}
```

---

### REVIEW RULES (Apply These):
{json.dumps(self.rules, indent=2)}

---

### RESPONSE FORMAT (MUST FOLLOW):

Organize your response with clear headers for each section above.
Be thorough, specific, and actionable.
If a section has no issues, state "No issues found in this category."
Always prioritize quality and user safety.

Generate your comprehensive QA review now:
"""
        return qa_prompt

    def generate_review(self, title, desc, diff):
        """Generate QA-focused review with caching and metrics"""
        # Validate diff size
        if len(diff) < Config.MIN_DIFF_CHARS:
            self.logger.warning("Diff size below minimum threshold")
            return "Error: Diff appears to be empty or too small for review."
        
        # Check cache
        if self.cache:
            cache_key = self._get_cache_key(title, desc, diff)
            cached_review = self.cache.get(cache_key)
            if cached_review:
                self.logger.info("Review retrieved from cache")
                return cached_review
        
        try:
            # Generate metrics for context
            metrics = None
            if Config.ENABLE_METRICS:
                metrics = MetricsAnalyzer.analyze(diff)
                self.logger.debug(f"PR Metrics: {metrics.to_dict()}")
            
            # Choose model
            model = self.router.choose_model(diff)
            prompt = self.build_prompt(title, desc, diff)
            
            # Generate QA review
            self.logger.info("Generating QA review...")
            qa_review = model.review(prompt)
            
            # Build formatted comment with QA sections and metrics
            formatted = build_markdown_comment(qa_review)
            
            # Add metrics if enabled
            if Config.ENABLE_METRICS and metrics:
                metrics_section = self._format_metrics(metrics)
                formatted += "\n" + metrics_section
            
            # Cache the result
            if self.cache:
                self.cache.set(cache_key, formatted)
            
            self.logger.info("QA review generated successfully")
            return formatted
        
        except Exception as e:
            self.logger.error(f"Error generating review: {e}")
            return f"Error generating review: {str(e)}"

    def _format_metrics(self, metrics) -> str:
        """Format metrics as markdown"""
        metrics_dict = metrics.to_dict()
        lines = ["\n---\n## PR Metrics"]
        lines.append(f"**Risk Level**: {metrics.risk_level}")
        lines.append(f"**Complexity Score**: {metrics_dict['complexity_score']}")
        lines.append(f"**Estimated Review Time**: {metrics_dict['estimated_review_time']}")
        lines.append(f"**Lines Changed**: +{metrics.total_lines_added} -{metrics.total_lines_removed}")
        lines.append(f"**Files Changed**: {metrics.files_changed}")
        
        if metrics.security_keywords_found:
            lines.append(f"**Security Keywords Detected**: {', '.join(metrics.security_keywords_found)}")
        
        return "\n".join(lines)
