from abc import ABC, abstractmethod
import requests
from datetime import datetime, timedelta
import time
import logging
from ..exceptions import SIEMConnectionError, SIEMAuthenticationError, SIEMResponseError, SIEMRateLimitError

logger = logging.getLogger(__name__)

class BaseSIEMConnector(ABC):
    """Base class for SIEM connectors"""
    
    def __init__(self, api_url, api_key):
        self.api_url = api_url.rstrip('/') if api_url else ""
        self.api_key = api_key
        self.session = requests.Session()
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        self.timeout = 30  # seconds
    
    @abstractmethod
    def authenticate(self):
        """Authenticate with the SIEM API"""
        pass
    
    @abstractmethod
    def fetch_logs(self, params=None):
        """Fetch logs from the SIEM"""
        pass
    
    @abstractmethod
    def normalize_log(self, log):
        """Convert SIEM-specific log format to standard format"""
        pass
    
    @abstractmethod
    def test_connection(self):
        """Test connection to SIEM API"""
        pass
    
    def _request_with_retry(self, method, endpoint, **kwargs):
        """Make HTTP request with retry logic"""
        if not self.api_url:
            raise SIEMConnectionError(self.get_siem_type(), "N/A", "API URL not configured")
        
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        retries = 0
        last_exception = None
        
        # Set default timeout if not provided
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.timeout
        
        while retries < self.max_retries:
            try:
                response = self.session.request(method, url, **kwargs)
                
                # Handle common error codes
                if response.status_code == 401:
                    raise SIEMAuthenticationError(
                        self.get_siem_type(), 
                        f"Authentication failed: {response.text}"
                    )
                elif response.status_code == 429:
                    raise SIEMRateLimitError(
                        self.get_siem_type(),
                        f"Rate limit exceeded: {response.text}"
                    )
                elif response.status_code >= 400:
                    raise SIEMResponseError(
                        self.get_siem_type(), 
                        response.status_code, 
                        f"Error response: {response.text}"
                    )
                
                return response
                
            except (requests.ConnectionError, requests.Timeout) as e:
                last_exception = e
                logger.warning(f"Connection error on {method} {url}: {str(e)}. Retry {retries+1}/{self.max_retries}")
                time.sleep(self.retry_delay * (2 ** retries))  # Exponential backoff
                retries += 1
            except (SIEMAuthenticationError, SIEMResponseError, SIEMRateLimitError):
                # Don't retry auth errors or specific SIEM errors
                raise
            except Exception as e:
                last_exception = e
                logger.warning(f"Unexpected error on {method} {url}: {str(e)}. Retry {retries+1}/{self.max_retries}")
                time.sleep(self.retry_delay * (2 ** retries))
                retries += 1
        
        # If we got here, all retries failed
        if isinstance(last_exception, (requests.ConnectionError, requests.Timeout)):
            raise SIEMConnectionError(
                self.get_siem_type(), 
                url, 
                f"Failed to connect after {self.max_retries} retries: {str(last_exception)}"
            )
        else:
            raise SIEMResponseError(
                self.get_siem_type(),
                None,
                f"Request failed after {self.max_retries} retries: {str(last_exception)}"
            )
    
    def get_siem_type(self):
        """Return the type of SIEM"""
        return self.__class__.__name__.replace('Connector', '')
    
    def get_time_range(self, minutes=30):
        """Get time range for log queries"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=minutes)
        return start_time, end_time
