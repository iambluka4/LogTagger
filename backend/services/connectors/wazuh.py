import json
import base64
from datetime import datetime
import time
import logging
from urllib.parse import urljoin
import requests
from .base import BaseSIEMConnector
from ..exceptions import SIEMAuthenticationError, SIEMResponseError

logger = logging.getLogger(__name__)

class WazuhConnector(BaseSIEMConnector):
    """Connector for Wazuh SIEM"""
    
    def __init__(self, api_url, api_key):
        super().__init__(api_url, api_key)
        self.token = None
        self.token_expiration = 0
    
    def authenticate(self):
        """Authenticate with Wazuh API using basic auth"""
        if not self.api_url or not self.api_key:
            raise SIEMAuthenticationError("Wazuh", "API credentials not configured")
        
        # Check if token is still valid
        now = time.time()
        if self.token and now < self.token_expiration:
            return self.token
        
        try:
            # Base64 encode the API key (user:password)
            auth_header = f"Basic {base64.b64encode(self.api_key.encode()).decode()}"
            
            response = self._request_with_retry(
                "POST", 
                "/security/user/authenticate",
                headers={"Authorization": auth_header}
            )
            
            data = response.json()
            if "data" in data and "token" in data["data"]:
                self.token = data["data"]["token"]
                # Set token expiration (default 1 hour minus 5 minutes for safety)
                self.token_expiration = now + 3300
                return self.token
            else:
                raise SIEMAuthenticationError("Wazuh", "Invalid authentication response")
        
        except Exception as e:
            if isinstance(e, SIEMAuthenticationError):
                raise
            raise SIEMAuthenticationError("Wazuh", f"Authentication failed: {str(e)}")
    
    def fetch_logs(self, params=None):
        """Fetch alerts from Wazuh"""
        params = params or {}
        
        # Get token
        token = self.authenticate()
        
        # Set up query parameters
        query_params = {
            "limit": params.get("limit", 100),
            "q": params.get("query", ""),
            "select": params.get("select", "*"),
            "sort": params.get("sort", "-timestamp"),
        }
        
        # Add time range if not specified
        if "from" not in query_params and "to" not in query_params:
            start_time, end_time = self.get_time_range(minutes=params.get("time_range", 30))
            query_params["from"] = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            query_params["to"] = end_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Make request
        response = self._request_with_retry(
            "GET",
            "/alerts",
            headers={"Authorization": f"Bearer {token}"},
            params=query_params
        )
        
        data = response.json()
        if "data" not in data or "affected_items" not in data["data"]:
            logger.warning(f"Unexpected Wazuh response format: {json.dumps(data)[:200]}...")
            return []
        
        # Process and normalize logs
        logs = []
        for item in data["data"]["affected_items"]:
            logs.append(self.normalize_log(item))
        
        return logs
    
    def normalize_log(self, log):
        """Convert Wazuh alert to standard format"""
        source_ip = log.get("agent", {}).get("ip", "unknown")
        if source_ip == "unknown" and "data" in log and "srcip" in log["data"]:
            source_ip = log["data"]["srcip"]
        
        severity_map = {
            1: "low", 2: "low", 3: "low",
            4: "medium", 5: "medium", 6: "medium",
            7: "high", 8: "high", 9: "high",
            10: "critical", 11: "critical", 12: "critical"
        }
        
        rule_id = log.get("rule", {}).get("id", "")
        severity = severity_map.get(log.get("rule", {}).get("level", 3), "low")
        
        # Return standardized log format
        return {
            "event_id": str(log.get("id", "")),
            "timestamp": log.get("timestamp", datetime.utcnow().isoformat()),
            "source_ip": source_ip,
            "severity": severity,
            "rule_name": log.get("rule", {}).get("description", ""),
            "siem_source": "wazuh",
            "raw_log": log
        }
    
    def test_connection(self):
        """Test connection to Wazuh API"""
        try:
            # Try to authenticate
            token = self.authenticate()
            
            # Make a simple request to verify token works
            response = self._request_with_retry(
                "GET",
                "/manager/info",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            data = response.json()
            if "data" in data:
                version = data["data"].get("version", "unknown")
                return {
                    "success": True,
                    "message": f"Successfully connected to Wazuh {version}",
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
            logger.error(f"Wazuh connection test failed: {str(e)}")
            return {
                "success": False,
                "message": f"Connection failed: {str(e)}",
                "details": {
                    "error_type": type(e).__name__,
                    "api_endpoint": self.api_url
                }
            }
