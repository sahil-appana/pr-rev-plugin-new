import os
import requests

class GroqClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('GROQ_API_KEY', '')
        self.url = os.getenv('GROQ_API_URL', 'https://api.groq.com/openai/v1/chat/completions')

    def review(self, prompt: str) -> str:
        if not self.api_key:
            return '[Groq Client] GROQ_API_KEY not set - skipping'
        headers = {'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}
        body = {
            'model': 'mixtral-8x7b-32768',
            'messages': [{'role': 'user', 'content': prompt}]
        }
        try:
            r = requests.post(self.url, headers=headers, json=body)
            r.raise_for_status()
            j = r.json()
            return j.get('choices', [{}])[0].get('message', {}).get('content', '')
        except Exception as e:
            return f'[Groq Error] {str(e)}'
