# AI PR Reviewer (Enterprise) - Bitbucket + Gemini 2.0 Flash

This repository contains a **production-ready, enterprise-grade PR review bot** for Bitbucket that uses **Gemini 2.0 Flash** and **Groq** for intelligent code analysis.

## ✨ Key Features

### Core Capabilities
- **Intelligent Code Review**: AI-powered analysis with security detection
- **Multi-Model Support**: Gemini 2.0 Flash + Groq with automatic fallback
- **Bitbucket Integration**: Full API support with inline comments
- **Production Ready**: Enterprise error handling, retries, and monitoring

### Advanced Features (NEW!)
- **PR Metrics & Analytics**: Complexity scoring, risk assessment, estimated review time
- **Review Caching**: 90%+ faster for repeated diffs
- **Comprehensive Logging**: Full audit trail for debugging
- **Rate Limit Handling**: Automatic backoff and retry logic
- **Security Analysis**: Detects dangerous patterns (eval, exec, credentials)
- **Inline Comments**: Comment on specific lines in PR
- **Reviewer Tracking**: Fetch assigned reviewers

### Architecture
- Modular design (core + models)
- Rules-driven prompts (rules/rules.json)
- Dry-run and local simulation modes
- 100% backward compatible

## 📋 Requirements

- Python 3.10+
- Environment variables (see Configuration)

## 🚀 Quick Start

### 1. Local Simulation (Recommended for Testing)
```bash
# Clone and setup
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run with sample diff
$env:GEMINI_API_KEY="your-key"  # PowerShell
python simulate_review.py sample_data/sample_diff.txt

# Or with metrics
$env:ENABLE_METRICS="true"
python simulate_review.py sample_data/sample_diff.txt
```

### 2. Production Deployment
```bash
# Set environment variables
$env:BITBUCKET_WORKSPACE="workspace"
$env:BITBUCKET_REPO_SLUG="repo"
$env:BITBUCKET_PR_ID="123"
$env:BITBUCKET_TOKEN="token"
$env:GEMINI_API_KEY="your-key"

# Run
python -m bot.main
```

## ⚙️ Configuration

### API Keys
```bash
GEMINI_API_KEY=                 # Required for Gemini
GROQ_API_KEY=                   # Optional for Groq
BITBUCKET_TOKEN=                # Required for Bitbucket
```

### Bitbucket Environment
```bash
BITBUCKET_WORKSPACE=myworkspace
BITBUCKET_REPO_SLUG=myrepo
BITBUCKET_PR_ID=123
BITBUCKET_TOKEN=<access-token>  # Use Bearer token
```

### Model Selection
```bash
MODEL_PROVIDER=auto             # 'auto', 'gemini', 'groq'
GEMINI_MODEL_NAME=gemini-2.0-flash
GROQ_MODEL_NAME=mixtral-8x7b-32768
```

### Review Configuration
```bash
MAX_DIFF_CHARS=14000            # Truncation threshold
MIN_DIFF_CHARS=10               # Minimum diff size
REQUEST_TIMEOUT=30              # API request timeout (seconds)
MAX_RETRIES=3                   # API retry attempts
RETRY_DELAY=2                   # Seconds between retries
```

### Feature Flags
```bash
DRY_RUN=false                   # true = don't post to Bitbucket
ENABLE_CACHING=true             # Cache review results
ENABLE_INLINE_COMMENTS=true     # Post line-level comments
ENABLE_METRICS=true             # Show PR metrics
VERBOSE_LOGGING=false           # Debug logging
```

### Cache
```bash
CACHE_TTL=3600                  # Cache expiration (seconds)
CACHE_DIR=.review_cache         # Cache directory
```

## 📊 What's New (Recent Enhancements)

See [ENHANCEMENTS.md](ENHANCEMENTS.md) for complete details on all new features:

- **Logger**: Comprehensive logging system with file output
- **Cache**: Review caching with TTL-based expiration
- **Metrics**: PR complexity, risk, security analysis
- **Bitbucket API**: Retry logic, rate limiting, inline comments
- **Review Engine**: Caching, metrics integration, better formatting
- **Configuration**: Centralized management with validation
- **Utilities**: New diff analysis functions

## 📈 Usage Examples

### Basic Review
```bash
python simulate_review.py diff.txt
```

### With Metrics
```bash
$env:ENABLE_METRICS="true"
python simulate_review.py diff.txt
```

### Dry Run (No Posting)
```bash
$env:DRY_RUN="true"
$env:BITBUCKET_WORKSPACE="workspace"
$env:BITBUCKET_REPO_SLUG="repo"
$env:BITBUCKET_PR_ID="123"
$env:BITBUCKET_TOKEN="token"
$env:GEMINI_API_KEY="key"
python -m bot.main
```

### With Detailed Logging
```bash
$env:VERBOSE_LOGGING="true"
python simulate_review.py diff.txt
```

## 🛠️ Development

### Project Structure
```
bot/
  __init__.py
  config.py                 # Configuration management
  main.py                   # Entry point
  core/
    bitbucket_api.py        # Bitbucket API client
    reviewer_engine.py      # Review generation
    model_router.py         # Model selection
    cache_manager.py        # Review caching (NEW)
    logger.py               # Logging system (NEW)
    metrics_analyzer.py     # PR metrics (NEW)
    comment_builder.py      # Comment formatting
    diff_fetcher.py         # Diff utilities
    utils.py                # General utilities
  models/
    gemini_client.py        # Gemini API client
    groq_client.py          # Groq API client
  rules/
    rules.json              # Review rules
```

### Adding New Features

1. **New Model**: Add to `bot/models/`, implement `review(prompt)` method
2. **New Analysis**: Extend `MetricsAnalyzer` in `bot/core/metrics_analyzer.py`
3. **New Config**: Add to `Config` class in `bot/config.py`
4. **New API Feature**: Add method to `BitbucketAPI` in `bot/core/bitbucket_api.py`

## 📝 Running in Bitbucket Pipelines

See `bitbucket-pipelines.yml`:
```yaml
image: python:3.11
pipelines:
  pull-requests:
    '**':
      - step:
          name: AI Code Review
          script:
            - pip install -r requirements.txt
            - python -m bot.main
          env:
            GEMINI_API_KEY: $GEMINI_API_KEY
            BITBUCKET_TOKEN: $BITBUCKET_TOKEN
```

## 🔒 Security Notes

- **Never commit API keys** - use Bitbucket repository variables
- **Bearer tokens**: Use full token, not "Bearer " prefix in env var
- **File-based cache**: Stored in `.review_cache/` (add to `.gitignore`)
- **Logs**: May contain diff content (use VERBOSE_LOGGING carefully in production)

## 🚨 Error Handling

The system includes:
- Automatic retry logic for transient errors
- Rate limit handling (respects Retry-After)
- Timeout protection (30s default)
- Graceful degradation (falls back to local mode)
- Comprehensive error logging

## 📚 Documentation

- [ENHANCEMENTS.md](ENHANCEMENTS.md) - Detailed feature documentation
- [CHANGES_SUMMARY.md](CHANGES_SUMMARY.md) - Complete changelog
- [requirements.txt](requirements.txt) - Dependencies

## 🎯 FAQ

**Q: How do I get the Bitbucket token?**
A: Create a Personal Access Token in Bitbucket (Settings > Access tokens)

**Q: Which model should I use?**
A: Default auto-mode works well. Use `gemini` for large diffs (>15KB), `groq` for smaller ones.

**Q: Does it work with GitHub?**
A: Currently Bitbucket only. GitHub integration planned for v2.

**Q: Can I run it locally without Bitbucket?**
A: Yes! Use `DRY_RUN=true` and `simulate_review.py` for testing.

**Q: How do I see metrics for a diff?**
A: Set `ENABLE_METRICS=true` in environment.

## 📄 License

See LICENSE file in repository.

## 🤝 Contributing

Contributions welcome! Please ensure tests pass and code follows project structure.

## 📞 Support

For issues or questions, please open a GitHub issue or contact the maintainers.

---

**Last Updated**: December 2025
**Version**: 2.0 (Enhanced Edition)
**Status**: Production Ready ✅
