import requests
from requests.exceptions import RequestException
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SIEMService:
    def __init__(self, api_url: str, api_key: str, siem_type: str):
        self.api_url = api_url
        self.api_key = api_key
        self.siem_type = siem_type.lower()
        
    def fetch_logs(self, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Fetch logs from the configured SIEM system"""
        if self.siem_type == "wazuh":
            return self._fetch_wazuh_logs(params)
        elif self.siem_type == "splunk":
            return self._fetch_splunk_logs(params)
        elif self.siem_type == "elastic":
            return self._fetch_elastic_logs(params)
        else:
            logger.error(f"Unsupported SIEM type: {self.siem_type}")
            return []
            
    def _fetch_wazuh_logs(self, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Fetch logs from Wazuh API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Default endpoint for Wazuh alerts
            endpoint = f"{self.api_url}/alerts"
            
            # Make the request
            response = requests.get(endpoint, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                # Normalize Wazuh alerts to our standardized format
                return self._normalize_wazuh_logs(data.get('data', []))
            else:
                logger.error(f"Error fetching from Wazuh API: {response.status_code} - {response.text}")
                return []
                
        except RequestException as e:
            logger.error(f"Request exception while fetching Wazuh logs: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching Wazuh logs: {str(e)}")
            return []
            
    def _normalize_wazuh_logs(self, logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize Wazuh logs to standardized format"""
        normalized_logs = []
        
        for log in logs:
            normalized_log = {
                "event_id": log.get("id", ""),
                "timestamp": log.get("timestamp", datetime.utcnow().isoformat()),
                "source_ip": log.get("data", {}).get("srcip", ""),
                "severity": self._map_wazuh_severity(log.get("rule", {}).get("level", 0)),
                "siem_source": "wazuh",
                "message": log.get("rule", {}).get("description", ""),
                "rule_name": log.get("rule", {}).get("id", ""),
                "raw_log": log
            }
            normalized_logs.append(normalized_log)
            
        return normalized_logs
        
    def _map_wazuh_severity(self, level: Union[int, str]) -> str:
        """Map Wazuh level to standardized severity"""
        level = int(level) if isinstance(level, str) else level
        
        if level <= 3:
            return "low"
        elif level <= 7:
            return "medium"
        elif level <= 10:
            return "high"
        else:
            return "critical"
            
    def _fetch_splunk_logs(self, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Fetch logs from Splunk API"""
        # Implementation for Splunk
        logger.info("Splunk integration to be implemented")
        return []
        
    def _fetch_elastic_logs(self, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Fetch logs from Elastic API"""
        # Implementation for Elastic
        logger.info("Elastic integration to be implemented")
        return []
