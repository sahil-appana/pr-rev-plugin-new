import os
import json
import hashlib
import time
from pathlib import Path
from typing import Optional

class CacheManager:
    """Simple file-based cache for review results"""
    
    def __init__(self, cache_dir: str = '.review_cache', ttl: int = 3600):
        self.cache_dir = Path(cache_dir)
        self.ttl = ttl
        self.cache_dir.mkdir(exist_ok=True)
    
    def _hash_key(self, key: str) -> str:
        """Generate hash for cache key"""
        return hashlib.sha256(key.encode()).hexdigest()
    
    def _get_cache_file(self, key: str) -> Path:
        """Get cache file path"""
        return self.cache_dir / f"{self._hash_key(key)}.json"
    
    def get(self, key: str) -> Optional[str]:
        """Get value from cache if not expired"""
        cache_file = self._get_cache_file(key)
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
                if time.time() - data['timestamp'] > self.ttl:
                    # Cache expired
                    cache_file.unlink()
                    return None
                return data['value']
        except Exception:
            return None
    
    def set(self, key: str, value: str) -> bool:
        """Store value in cache"""
        try:
            cache_file = self._get_cache_file(key)
            data = {
                'key': key,
                'value': value,
                'timestamp': time.time()
            }
            with open(cache_file, 'w') as f:
                json.dump(data, f)
            return True
        except Exception:
            return False
    
    def clear(self) -> None:
        """Clear all cached items"""
        try:
            for f in self.cache_dir.glob('*.json'):
                f.unlink()
        except Exception:
            pass
    
    def cleanup_expired(self) -> int:
        """Remove expired cache entries, return count removed"""
        count = 0
        try:
            for f in self.cache_dir.glob('*.json'):
                with open(f, 'r') as file:
                    data = json.load(file)
                    if time.time() - data['timestamp'] > self.ttl:
                        f.unlink()
                        count += 1
        except Exception:
            pass
        return count
