import requests
import json
import logging
from typing import Dict, List, Any, Optional, Tuple

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MLService:
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.api_key = api_key
        
    def classify_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Send events to ML/LLM API for classification and tagging
        Returns events with added ML tags
        """
        try:
            if not self.api_url or not self.api_key:
                logger.warning("ML API URL or key not configured")
                return events
                
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Prepare payload
            payload = {
                "events": events
            }
            
            # Make request to ML API
            response = requests.post(
                f"{self.api_url}/classify", 
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("classified_events", events)
            else:
                logger.error(f"ML API returned error: {response.status_code} - {response.text}")
                return events
                
        except Exception as e:
            logger.error(f"Error while classifying events with ML API: {str(e)}")
            return events
    
    def analyze_event(self, event: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Analyze a single security event and return extracted classifications
        Returns a tuple of (ml_labels, mitre_mappings)
        """
        try:
            if not self.api_url or not self.api_key:
                logger.warning("ML API URL or key not configured")
                return {}, {}
                
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Make request to ML API
            response = requests.post(
                f"{self.api_url}/analyze", 
                headers=headers,
                json={"event": event},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("ml_labels", {}), result.get("mitre_mappings", {})
            else:
                logger.error(f"ML API returned error: {response.status_code} - {response.text}")
                return {}, {}
                
        except Exception as e:
            logger.error(f"Error while analyzing event with ML API: {str(e)}")
            return {}, {}
    
    def get_mitre_techniques(self) -> List[Dict[str, Any]]:
        """Get MITRE ATT&CK techniques from the ML API or local cache"""
        try:
            if not self.api_url or not self.api_key:
                logger.warning("ML API URL or key not configured")
                return []
                
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Make request to ML API
            response = requests.get(
                f"{self.api_url}/mitre/techniques", 
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get("techniques", [])
            else:
                logger.error(f"ML API returned error: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error while fetching MITRE techniques: {str(e)}")
            return []
    
    def get_mitre_tactics(self) -> List[Dict[str, Any]]:
        """Get MITRE ATT&CK tactics from the ML API or local cache"""
        try:
            if not self.api_url or not self.api_key:
                logger.warning("ML API URL or key not configured")
                return []
                
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Make request to ML API
            response = requests.get(
                f"{self.api_url}/mitre/tactics", 
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get("tactics", [])
            else:
                logger.error(f"ML API returned error: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error while fetching MITRE tactics: {str(e)}")
            return []
