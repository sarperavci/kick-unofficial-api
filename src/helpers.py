from typing import Dict, Tuple, Optional, Any
import time
import curl_cffi.requests as requests
from dataclasses import dataclass
from urllib.parse import urljoin
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CloudflareConfig:
    bypass_server_url: str = os.getenv("BYPASS_SERVER_URL", "http://localhost")
    port: int = os.getenv("BYPASS_SERVER_PORT", 8000)
    target_url: str = os.getenv("TARGET_URL", "https://kick.com")
    
    @property
    def bypass_endpoint(self) -> str:
        return f"{self.bypass_server_url}:{self.port}/cookies"

class RequestError(Exception):
    """Custom exception for request-related errors"""
    pass

class CloudflareBypassError(RequestError):
    """Exception raised when Cloudflare bypass fails"""
    pass

class APIResponse:
    def __init__(self, status_code: int, data: Optional[Dict] = None, error: Optional[str] = None):
        self.status_code = status_code
        self.data = data
        self.error = error
        
    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300 and self.error is None

class KickAPI:
    def __init__(self, cf_config: Optional[CloudflareConfig] = None):
        self.cf_config = cf_config or CloudflareConfig()
        self.bypass_data: Tuple[Optional[Dict], Optional[str]] = (None, None)
        
    def _make_request(
        self,
        url: str,
        method: str,
        cf_clearance_cookies: Dict,
        user_agent: str,
        auth: Optional[str] = None,
        json_data: Optional[Dict] = None,
    ) -> APIResponse:
        """
        Make an HTTP request with Cloudflare bypass data
        """
        headers = {"User-Agent": user_agent}
        if auth:
            headers["Authorization"] = auth

        try:
            response = requests.request(
                method,
                url,
                headers=headers,
                cookies=cf_clearance_cookies,
                json=json_data,
                timeout=10
            )
            
            return APIResponse(
                status_code=response.status_code,
                data=response.json() if response.content else None
            )
            
        except requests.RequestsError as e:
            logger.error(f"Request failed: {str(e)}")
            return APIResponse(status_code=500, error=str(e))
        except ValueError as e:
            logger.error(f"JSON decode failed: {str(e)}")
            return APIResponse(status_code=500, error="Invalid JSON response")

    def _get_cf_clearance(self, retry: int = 3) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Get Cloudflare clearance cookies and user agent
        """
        for attempt in range(retry):
            try:
                response = requests.get(
                    self.cf_config.bypass_endpoint,
                    params={"url": self.cf_config.target_url},
                    timeout=60
                )
                
                if response.status_code != 200:
                    raise CloudflareBypassError(f"Bypass server returned status {response.status_code}")
                
                data = response.json()
                return data["cookies"], data["user_agent"]
                
            except Exception as e:
                logger.warning(f"Cloudflare bypass attempt {attempt + 1}/{retry} failed: {str(e)}")
                if attempt < retry - 1:
                    time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                    
        raise CloudflareBypassError("Failed to obtain Cloudflare clearance")

    def send_request(
        self,
        endpoint: str,
        method: str = "GET",
        auth: Optional[str] = None,
        json_data: Optional[Dict] = None,
        retry: int = 3
    ) -> APIResponse:
        """
        Send an API request with automatic Cloudflare bypass handling
        
        Args:
            endpoint: API endpoint path
            method: HTTP method
            auth: Authorization token
            json_data: Request body for POST/PUT requests
            retry: Number of retry attempts
            
        Returns:
            APIResponse object containing status code and response data
        """
        url = urljoin(self.cf_config.target_url, endpoint)
        
        for attempt in range(retry):
            try:
                # Get or refresh Cloudflare bypass data if needed
                if not all(self.bypass_data):
                    self.bypass_data = self._get_cf_clearance()
                
                cookies, user_agent = self.bypass_data
                response = self._make_request(
                    url=url,
                    method=method,
                    cf_clearance_cookies=cookies,
                    user_agent=user_agent,
                    auth=auth,
                    json_data=json_data
                )
                
                if response.is_success:
                    return response
                
                # Reset bypass data if request failed
                self.bypass_data = (None, None)
                
            except Exception as e:
                logger.error(f"Request attempt {attempt + 1}/{retry} failed: {str(e)}")
                self.bypass_data = (None, None)
                
            if attempt < retry - 1:
                time.sleep(0.5 * (attempt + 1))
                
        return APIResponse(status_code=500, error="Max retries exceeded")
