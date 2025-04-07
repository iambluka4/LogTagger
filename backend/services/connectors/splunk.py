import json
import logging
import time
from datetime import datetime
from .base import BaseSIEMConnector
from ..exceptions import SIEMAuthenticationError, SIEMResponseError

logger = logging.getLogger(__name__)

class SplunkConnector(BaseSIEMConnector):
    """Connector for Splunk SIEM"""
    
    def __init__(self, api_url, api_key):
        super().__init__(api_url, api_key)
        self.session_key = None
        self.session_expiration = 0
    
    def authenticate(self):
        """Authenticate with Splunk API"""
        if not self.api_url or not self.api_key:
            raise SIEMAuthenticationError("Splunk", "API credentials not configured")
        
        # Check if session is still valid
        now = time.time()
        if self.session_key and now < self.session_expiration:
            return self.session_key
        
        try:
            response = self._request_with_retry(
                "POST",
                "/services/auth/login",
                data={"username": "admin", "password": self.api_key},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                params={"output_mode": "json"}
            )
            
            data = response.json()
            if "sessionKey" in data:
                self.session_key = data["sessionKey"]
                # Set session expiration (default 1 hour minus 5 minutes for safety)
                self.session_expiration = now + 3300
                return self.session_key
            else:
                raise SIEMAuthenticationError("Splunk", "Invalid authentication response")
        
        except Exception as e:
            if isinstance(e, SIEMAuthenticationError):
                raise
            raise SIEMAuthenticationError("Splunk", f"Authentication failed: {str(e)}")
    
    def fetch_logs(self, params=None):
        """Fetch events from Splunk"""
        params = params or {}
        
        # Get session key
        session_key = self.authenticate()
        
        # Set up search parameters
        start_time, end_time = self.get_time_range(minutes=params.get("time_range", 30))
        time_range = f"earliest_time={start_time.strftime('%Y-%m-%dT%H:%M:%S')}&latest_time={end_time.strftime('%Y-%m-%dT%H:%M:%S')}"
        
        # Create search job
        search_query = params.get("query", "search index=_internal | head 100")
        search_params = {
            "search": search_query,
            "earliest_time": start_time.strftime("%Y-%m-%dT%H:%M:%S"),
            "latest_time": end_time.strftime("%Y-%m-%dT%H:%M:%S"),
            "output_mode": "json"
        }
        
        # Start search job
        response = self._request_with_retry(
            "POST",
            "/services/search/jobs",
            headers={"Authorization": f"Splunk {session_key}"},
            data=search_params
        )
        
        data = response.json()
        job_sid = data.get("sid")
        if not job_sid:
            raise SIEMResponseError("Splunk", response.status_code, "Failed to create search job")
        
        # Wait for job to complete
        complete = False
        retries = 0
        max_job_retries = 10
        
        while not complete and retries < max_job_retries:
            status_response = self._request_with_retry(
                "GET",
                f"/services/search/jobs/{job_sid}",
                headers={"Authorization": f"Splunk {session_key}"},
                params={"output_mode": "json"}
            )
            
            status_data = status_response.json()
            if status_data.get("entry", [{}])[0].get("content", {}).get("isDone"):
                complete = True
            else:
                time.sleep(1)
                retries += 1
        
        if not complete:
            raise SIEMResponseError("Splunk", None, f"Search job timed out after {max_job_retries} checks")
        
        # Get search results
        results_response = self._request_with_retry(
            "GET",
            f"/services/search/jobs/{job_sid}/results",
            headers={"Authorization": f"Splunk {session_key}"},
            params={"output_mode": "json", "count": params.get("limit", 100)}
        )
        
        results_data = results_response.json()
        if "results" not in results_data:
            logger.warning(f"Unexpected Splunk response format: {json.dumps(results_data)[:200]}...")
            return []
        
        # Process and normalize logs
        logs = []
        for result in results_data["results"]:
            logs.append(self.normalize_log(result))
        
        return logs
    
    def normalize_log(self, log):
        """Convert Splunk event to standard format"""
        # Extract source IP from various Splunk fields
        source_ip = log.get("src_ip", log.get("src", log.get("source_ip", "unknown")))
        
        # Map Splunk severity to standardized values
        severity_field = log.get("severity", log.get("severity_label", log.get("priority", "low")))
        severity_map = {
            "debug": "low",
            "info": "low",
            "information": "low",
            "notice": "low",
            "warning": "medium",
            "error": "high",
            "critical": "critical",
            "alert": "critical",
            "emergency": "critical"
        }
        severity = severity_map.get(str(severity_field).lower(), "medium")
        
        # Extract timestamp
        event_time = log.get("_time", log.get("timestamp", datetime.utcnow().isoformat()))
        
        # Generate a unique event ID if not present
        event_id = log.get("_cd", log.get("event_id", log.get("id", str(hash(json.dumps(log))))))
        
        # Return standardized log format
        return {
            "event_id": str(event_id),
            "timestamp": event_time,
            "source_ip": source_ip,
            "severity": severity,
            "rule_name": log.get("rule_name", log.get("signature", log.get("description", ""))),
            "siem_source": "splunk",
            "raw_log": log
        }
    
    def test_connection(self):
        """Test connection to Splunk API"""
        try:
            # Try to authenticate
            session_key = self.authenticate()
            
            # Make a simple request to verify session key works
            response = self._request_with_retry(
                "GET",
                "/services/server/info",
                headers={"Authorization": f"Splunk {session_key}"},
                params={"output_mode": "json"}
            )
            
            data = response.json()
            if "entry" in data and len(data["entry"]) > 0:
                version = data["entry"][0].get("content", {}).get("version", "unknown")
                return {
                    "success": True,
                    "message": f"Successfully connected to Splunk {version}",
                    "details": {
                        "version": version,
                        "api_endpoint": self.api_url
                    }
                }
            else:
                return {
                    "success": False,
                    "message": "Connection successful but unexpected response format",
                    "details": {
                        "api_endpoint": self.api_url
                    }
                }
        
        except Exception as e:
            logger.error(f"Splunk connection test failed: {str(e)}")
            return {
                "success": False,
                "message": f"Connection failed: {str(e)}",
                "details": {
                    "error_type": type(e).__name__,
                    "api_endpoint": self.api_url
                }
            }
