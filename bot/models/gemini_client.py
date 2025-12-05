import os
import google.generativeai as genai

class GeminiClient:
    def __init__(self, api_key: str = None):
        key = api_key or os.getenv('GEMINI_API_KEY')
        if not key:
            raise RuntimeError('GEMINI_API_KEY not set for GeminiClient')
        genai.configure(api_key=key)
        # model name is configurable via ENV (defaults to gemini-2.0-flash)
        self.model_name = os.getenv('GEMINI_MODEL_NAME', 'gemini-2.0-flash')

    def review(self, prompt: str) -> str:
        try:
            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content(prompt)
            # .text property contains string output for many sdk versions
            return getattr(response, 'text', str(response))
        except Exception as e:
            return f"[Gemini Error] {str(e)}"
