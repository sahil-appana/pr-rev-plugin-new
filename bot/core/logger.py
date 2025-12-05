import logging
import sys
from pathlib import Path
from typing import Optional

class ReviewLogger:
    """Centralized logging for review system"""
    
    _logger: Optional[logging.Logger] = None
    
    @classmethod
    def setup(cls, verbose: bool = False, log_file: Optional[str] = None) -> logging.Logger:
        """Initialize logger with optional file output"""
        if cls._logger:
            return cls._logger
        
        cls._logger = logging.getLogger('ai_pr_reviewer')
        level = logging.DEBUG if verbose else logging.INFO
        cls._logger.setLevel(level)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        cls._logger.addHandler(console_handler)
        
        # File handler if specified
        if log_file:
            try:
                Path(log_file).parent.mkdir(parents=True, exist_ok=True)
                file_handler = logging.FileHandler(log_file)
                file_handler.setLevel(level)
                file_handler.setFormatter(formatter)
                cls._logger.addHandler(file_handler)
            except Exception as e:
                cls._logger.warning(f"Could not setup file logging: {e}")
        
        return cls._logger
    
    @classmethod
    def get(cls) -> logging.Logger:
        """Get logger instance"""
        if not cls._logger:
            cls.setup()
        return cls._logger
    
    @classmethod
    def debug(cls, msg: str, *args, **kwargs) -> None:
        cls.get().debug(msg, *args, **kwargs)
    
    @classmethod
    def info(cls, msg: str, *args, **kwargs) -> None:
        cls.get().info(msg, *args, **kwargs)
    
    @classmethod
    def warning(cls, msg: str, *args, **kwargs) -> None:
        cls.get().warning(msg, *args, **kwargs)
    
    @classmethod
    def error(cls, msg: str, *args, **kwargs) -> None:
        cls.get().error(msg, *args, **kwargs)
    
    @classmethod
    def critical(cls, msg: str, *args, **kwargs) -> None:
        cls.get().critical(msg, *args, **kwargs)
