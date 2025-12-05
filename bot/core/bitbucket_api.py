import os
import requests
import json
import time
from typing import Tuple, Optional, Dict, List
from bot.config import Config
from bot.core.logger import ReviewLogger

# Enhanced Bitbucket API helper with error handling and inline comments support.
class BitbucketAPI:
    def __init__(self):
        self.workspace = Config.BITBUCKET_WORKSPACE
        self.repo_slug = Config.BITBUCKET_REPO_SLUG
        self.pr_id = Config.BITBUCKET_PR_ID
        self.access_token = Config.BITBUCKET_TOKEN
        self.base_url = Config.BITBUCKET_BASE_URL
        self.timeout = Config.REQUEST_TIMEOUT
        self.max_retries = Config.MAX_RETRIES
        self.retry_delay = Config.RETRY_DELAY
        
        self.base = None
        if self.workspace and self.repo_slug:
            self.base = f"{self.base_url}/repositories/{self.workspace}/{self.repo_slug}"
        
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        self.logger = ReviewLogger.get()

    def _make_request(self, method: str, url: str, **kwargs) -> Optional[Dict]:
        """Make HTTP request with retry logic and error handling"""
        for attempt in range(self.max_retries):
            try:
                resp = self._execute_request(method, url, **kwargs)
                
                if resp.status_code == 429:  # Rate limited
                    self._handle_rate_limit(resp)
                    continue
                
                resp.raise_for_status()
                return resp.json() if method.upper() == 'GET' else None
            
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                self._handle_retry(e, attempt)
            except requests.exceptions.HTTPError as e:
                return self._handle_http_error(e, resp, attempt)
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                return None
        
        self.logger.error(f"Failed after {self.max_retries} retries")
        return None

    def _execute_request(self, method: str, url: str, **kwargs):
        """Execute the actual HTTP request"""
        if method.upper() == 'GET':
            return requests.get(url, headers=self.headers, timeout=self.timeout, verify=True, **kwargs)
        elif method.upper() == 'POST':
            return requests.post(url, headers=self.headers, timeout=self.timeout, verify=True, **kwargs)
        else:
            raise ValueError(f"Unsupported method: {method}")

    def _handle_rate_limit(self, resp) -> None:
        """Handle rate limit response"""
        wait_time = int(resp.headers.get('Retry-After', self.retry_delay))
        self.logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
        time.sleep(wait_time)

    def _handle_retry(self, error, attempt: int) -> None:
        """Handle retry logic for transient errors"""
        self.logger.warning(f"{type(error).__name__} (attempt {attempt + 1}/{self.max_retries})")
        if attempt < self.max_retries - 1:
            time.sleep(self.retry_delay)

    def _handle_http_error(self, error, resp, attempt: int) -> Optional[Dict]:
        """Handle HTTP errors"""
        if 400 <= resp.status_code < 500:
            self.logger.error(f"HTTP {resp.status_code}: {resp.text}")
            return None
        # Server error - retry
        self.logger.warning(f"HTTP {resp.status_code} (attempt {attempt + 1}/{self.max_retries})")
        if attempt < self.max_retries - 1:
            time.sleep(self.retry_delay)
        return None

    def get_pr_metadata(self) -> Tuple[str, str]:
        """Get PR title and description with fallback"""
        if not self.base or not self.pr_id:
            self.logger.debug("No Bitbucket context - using fallback metadata")
            return ("Local Simulation PR", "No description (simulation)")
        
        url = f"{self.base}/pullrequests/{self.pr_id}"
        try:
            data = self._make_request('GET', url)
            if data:
                return (data.get('title', ''), data.get('description', ''))
        except Exception as e:
            self.logger.error(f"Error fetching PR metadata: {e}")
        
        return ("PR Review", "Unable to fetch description")

    def get_pr_diff(self) -> str:
        """Get PR diff with fallback to sample"""
        if not self.base or not self.pr_id:
            self.logger.debug("No Bitbucket context - using sample diff")
            sample = os.path.join(os.getcwd(), 'sample_data', 'sample_diff.txt')
            if os.path.exists(sample):
                with open(sample, 'r', encoding='utf-8') as f:
                    return f.read()
            return ''
        
        url = f"{self.base}/pullrequests/{self.pr_id}/diff"
        try:
            resp = requests.get(url, headers=self.headers, timeout=self.timeout, verify=True)
            resp.raise_for_status()
            self.logger.info("Successfully fetched PR diff")
            return resp.text
        except Exception as e:
            self.logger.error(f"Error fetching PR diff: {e}")
            return ''

    def post_comment(self, comment_text: str) -> bool:
        """Post comment to PR with error handling"""
        if Config.DRY_RUN:
            self.logger.info("DRY_RUN enabled - would post comment")
            print(comment_text)
            return True
        
        if not self.base or not self.pr_id:
            self.logger.warning("No Bitbucket context - comment not posted")
            return False
        
        url = f"{self.base}/pullrequests/{self.pr_id}/comments"
        payload = {"content": {"raw": comment_text}}
        
        try:
            resp = requests.post(url, headers=self.headers, json=payload, 
                               timeout=self.timeout, verify=True)
            
            if resp.status_code in (200, 201):
                self.logger.info("Comment posted successfully")
                return True
            else:
                self.logger.error(f"Failed to post comment: {resp.status_code} - {resp.text}")
                return False
        except Exception as e:
            self.logger.error(f"Error posting comment: {e}")
            return False

    def post_inline_comment(self, file_path: str, line_number: int, comment_text: str) -> bool:
        """Post inline comment on specific file/line for QA issues"""
        if not Config.ENABLE_QA_INLINE_COMMENTS:
            return False
        
        if not self.base or not self.pr_id:
            self.logger.warning("No Bitbucket context for inline comment")
            return False
        
        # Bitbucket inline comments require specific payload structure
        url = f"{self.base}/pullrequests/{self.pr_id}/comments"
        payload = {
            "content": {"raw": comment_text},
            "inline": {
                "to": line_number,
                "path": file_path
            }
        }
        
        try:
            resp = requests.post(url, headers=self.headers, json=payload,
                               timeout=self.timeout, verify=True)
            
            if resp.status_code in (200, 201):
                self.logger.debug(f"Inline comment posted on {file_path}:{line_number}")
                return True
            else:
                self.logger.warning(f"Failed to post inline comment: {resp.status_code}")
                return False
        except Exception as e:
            self.logger.error(f"Error posting inline comment: {e}")
            return False

    def get_reviewers(self) -> List[str]:
        """Get list of PR reviewers"""
        if not self.base or not self.pr_id:
            return []
        
        url = f"{self.base}/pullrequests/{self.pr_id}/reviewers"
        try:
            data = self._make_request('GET', url)
            if data and 'values' in data:
                return [r.get('username') for r in data['values'] if r.get('username')]
        except Exception as e:
            self.logger.warning(f"Error fetching reviewers: {e}")
        
        return []
