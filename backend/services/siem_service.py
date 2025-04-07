import requests
from requests.exceptions import RequestException
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

# Виправлені імпорти на відносні для того ж пакета
from .connectors.wazuh import WazuhConnector
from .connectors.splunk import SplunkConnector
from .connectors.elastic import ElasticConnector
from .exceptions import SIEMException

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SIEMService:
    """Service for interacting with SIEM systems"""
    
    def __init__(self, api_url=None, api_key=None, siem_type=None):
        """Initialize SIEM service with connector"""
        self.connector = self._create_connector(api_url, api_key, siem_type)
    
    def _create_connector(self, api_url, api_key, siem_type):
        """Factory method to create appropriate connector"""
        if not siem_type:
            raise ValueError("SIEM type must be specified")
            
        if siem_type.lower() == "wazuh":
            return WazuhConnector(api_url, api_key)
        elif siem_type.lower() == "splunk":
            return SplunkConnector(api_url, api_key)
        elif siem_type.lower() == "elastic":
            return ElasticConnector(api_url, api_key)
        else:
            raise ValueError(f"Unsupported SIEM type: {siem_type}")
    
    def fetch_logs(self, params=None):
        """Fetch logs from SIEM system"""
        try:
            return self.connector.fetch_logs(params)
        except SIEMException as e:
            logger.error(f"SIEM exception: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching logs: {str(e)}")
            return []
    
    def test_connection(self):
        """Test connection to SIEM system"""
        try:
            return self.connector.test_connection()
        except Exception as e:
            logger.error(f"Test connection failed: {str(e)}")
            return {
                "success": False,
                "message": f"Connection test failed: {str(e)}",
                "details": {
                    "error_type": type(e).__name__
                }
            }
