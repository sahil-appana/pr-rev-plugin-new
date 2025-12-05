import os
from typing import Optional

class Config:
    """Centralized configuration with validation and defaults"""
    
    # API Configuration
    MODEL_PROVIDER = os.getenv('MODEL_PROVIDER', 'auto')  # 'auto', 'gemini', 'groq'
    GEMINI_MODEL_NAME = os.getenv('GEMINI_MODEL_NAME', 'gemini-2.0-flash')
    GROQ_MODEL_NAME = os.getenv('GROQ_MODEL_NAME', 'mixtral-8x7b-32768')
    
    # Bitbucket Configuration
    BITBUCKET_WORKSPACE = os.getenv('BITBUCKET_WORKSPACE', '')
    BITBUCKET_REPO_SLUG = os.getenv('BITBUCKET_REPO_SLUG', '')
    BITBUCKET_PR_ID = os.getenv('BITBUCKET_PR_ID', '')
    BITBUCKET_TOKEN = os.getenv('BITBUCKET_TOKEN', '')
    BITBUCKET_BASE_URL = os.getenv('BITBUCKET_BASE_URL', 'https://api.bitbucket.org/2.0')
    
    # Review Configuration
    MAX_DIFF_CHARS = int(os.getenv('MAX_DIFF_CHARS', '14000'))
    MIN_DIFF_CHARS = int(os.getenv('MIN_DIFF_CHARS', '10'))
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30'))
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
    RETRY_DELAY = int(os.getenv('RETRY_DELAY', '2'))
    
    # Feature Flags
    DRY_RUN = os.getenv('DRY_RUN', 'false').lower() == 'true'
    ENABLE_CACHING = os.getenv('ENABLE_CACHING', 'true').lower() == 'true'
    ENABLE_INLINE_COMMENTS = os.getenv('ENABLE_INLINE_COMMENTS', 'true').lower() == 'true'
    ENABLE_TASK_CREATION = os.getenv('ENABLE_TASK_CREATION', 'false').lower() == 'true'
    ENABLE_METRICS = os.getenv('ENABLE_METRICS', 'true').lower() == 'true'
    VERBOSE_LOGGING = os.getenv('VERBOSE_LOGGING', 'false').lower() == 'true'
    QA_MODE = True  # QA Mode ALWAYS ACTIVE - Cannot be disabled
    ENABLE_QA_INLINE_COMMENTS = os.getenv('ENABLE_QA_INLINE_COMMENTS', 'true').lower() == 'true'
    
    # Cache Configuration
    CACHE_TTL = int(os.getenv('CACHE_TTL', '3600'))  # 1 hour
    CACHE_DIR = os.getenv('CACHE_DIR', '.review_cache')
    
    @classmethod
    def validate(cls) -> Optional[str]:
        """Validate configuration and return error message if invalid"""
        if cls.MODEL_PROVIDER not in ['auto', 'gemini', 'groq']:
            return f"Invalid MODEL_PROVIDER: {cls.MODEL_PROVIDER}"
        if cls.MAX_DIFF_CHARS < 100:
            return "MAX_DIFF_CHARS must be at least 100"
        if cls.REQUEST_TIMEOUT < 5:
            return "REQUEST_TIMEOUT must be at least 5 seconds"
        return None
    
    @classmethod
    def get_bitbucket_context(cls) -> bool:
        """Check if running in Bitbucket environment"""
        return bool(cls.BITBUCKET_WORKSPACE and cls.BITBUCKET_REPO_SLUG and cls.BITBUCKET_PR_ID)

# Export for backward compatibility
MODEL_PROVIDER = Config.MODEL_PROVIDER
DRY_RUN = Config.DRY_RUN
GEMINI_MODEL_NAME = Config.GEMINI_MODEL_NAME
