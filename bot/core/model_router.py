import os
from bot.models.gemini_client import GeminiClient
from bot.models.groq_client import GroqClient
from bot.core.logger import ReviewLogger

class ModelRouter:
    def __init__(self):
        self.provider = os.getenv('MODEL_PROVIDER', 'auto')
        self.logger = ReviewLogger.get()
        
        try:
            self.gemini = GeminiClient(api_key=os.getenv('GEMINI_API_KEY'))
            self.logger.debug("Gemini client initialized")
        except Exception as e:
            self.logger.warning(f"Gemini client init failed: {e}")
            self.gemini = None
        
        try:
            self.groq = GroqClient(api_key=os.getenv('GROQ_API_KEY', ''))
            self.logger.debug("Groq client initialized")
        except Exception as e:
            self.logger.warning(f"Groq client init failed: {e}")
            self.groq = None

    def choose_model(self, diff_text: str):
        """Choose model based on provider and diff size"""
        if self.provider == 'gemini':
            if not self.gemini:
                raise RuntimeError("Gemini model requested but not available")
            return self.gemini
        
        if self.provider == 'groq':
            if not self.groq:
                raise RuntimeError("Groq model requested but not available")
            return self.groq
        
        # auto - choose based on diff size
        if len(diff_text) < 15000:
            if self.groq:
                self.logger.debug("Selected Groq for smaller diff")
                return self.groq
            elif self.gemini:
                self.logger.debug("Groq not available, falling back to Gemini")
                return self.gemini
        else:
            if self.gemini:
                self.logger.debug("Selected Gemini for larger diff")
                return self.gemini
            elif self.groq:
                self.logger.debug("Gemini not available, falling back to Groq")
                return self.groq
        
        raise RuntimeError("No model providers available")
