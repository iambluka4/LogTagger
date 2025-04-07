import json
import logging
from datetime import datetime
from .base import BaseSIEMConnector
from ..exceptions import SIEMAuthenticationError, SIEMResponseError

logger = logging.getLogger(__name__)

class ElasticConnector(BaseSIEMConnector):
    """Connector for Elastic SIEM"""
    
    def __init__(self, api_url, api_key):
        super().__init__(api_url, api_key)
    
    def authenticate(self):
        """Authenticate with Elastic API using API key"""
        if not self.api_url or not self.api_key:
            raise SIEMAuthenticationError("Elastic", "API credentials not configured")
        
        # For Elastic, authentication is handled per-request
        # Just verify API key is properly formatted
        if not self.api_key:
            raise SIEMAuthenticationError("Elastic", "API key not provided")
        
        return self.api_key
    
    def fetch_logs(self, params=None):
        """Fetch events from Elastic"""
        params = params or {}
        
        # Verify authentication
        api_key = self.authenticate()
        
        # Determine index to search
        index = params.get("index", "filebeat-*")
        
        # Set up time range
        start_time, end_time = self.get_time_range(minutes=params.get("time_range", 30))
        
        # Build search query
        query = {
            "size": params.get("limit", 100),
            "query": {
                "bool": {
                    "must": [
                        {
                            "range": {
                                "@timestamp": {
                                    "gte": start_time.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                                    "lte": end_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
                                }
                            }
                        }
                    ]
                }
            },
            "sort": [{"@timestamp": {"order": "desc"}}]
        }
        
        # Add user-provided query if available
        if "query" in params:
            query["query"]["bool"]["must"].append({
                "query_string": {"query": params["query"]}
            })
        
        # Make search request
        response = self._request_with_retry(
            "POST",
            f"/{index}/_search",
            json=query,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"ApiKey {api_key}"
            }
        )
        
        data = response.json()
        if "hits" not in data or "hits" not in data["hits"]:
            logger.warning(f"Unexpected Elastic response format: {json.dumps(data)[:200]}...")
            return []
        
        # Process and normalize logs
        logs = []
        for hit in data["hits"]["hits"]:
            logs.append(self.normalize_log(hit))
        
        return logs
    
    def normalize_log(self, log):
        """Convert Elastic document to standard format"""
        # Extract source data
        source = log.get("_source", {})
        
        # Extract source IP from various Elastic fields
        source_ip = "unknown"
        if "source" in source and "ip" in source["source"]:
            source_ip = source["source"]["ip"]
        elif "client" in source and "ip" in source["client"]:
            source_ip = source["client"]["ip"]
        elif "host" in source and "ip" in source["host"]:
            source_ip = source["host"]["ip"][0] if isinstance(source["host"]["ip"], list) else source["host"]["ip"]
        
        # Map severity from various fields
        severity = "medium"
        if "event" in source and "severity" in source["event"]:
            sev_val = source["event"]["severity"]
            if isinstance(sev_val, int):
                if sev_val <= 3:
                    severity = "low"
                elif sev_val <= 6:
                    severity = "medium"
                elif sev_val <= 8:
                    severity = "high"
                else:
                    severity = "critical"
            elif isinstance(sev_val, str):
                sev_map = {
                    "info": "low", "low": "low",
                    "warning": "medium", "medium": "medium",
                    "error": "high", "high": "high",
                    "critical": "critical"
                }
                severity = sev_map.get(sev_val.lower(), "medium")
        
        # Get rule name if available
        rule_name = ""
        if "rule" in source and "description" in source["rule"]:
            rule_name = source["rule"]["description"]
        elif "rule" in source and "name" in source["rule"]:
            rule_name = source["rule"]["name"]
        
        # Return standardized log format
        return {
            "event_id": log.get("_id", ""),
            "timestamp": source.get("@timestamp", datetime.utcnow().isoformat()),
            "source_ip": source_ip,
            "severity": severity,
            "rule_name": rule_name,
            "siem_source": "elastic",
            "raw_log": log
        }
    
    def test_connection(self):
        """Test connection to Elastic API"""
        try:
            # Verify authentication
            api_key = self.authenticate()
            
            # Make a simple request to verify API key works
            response = self._request_with_retry(
                "GET",
                "/",
                headers={"Authorization": f"ApiKey {api_key}"}
            )
            
            data = response.json()
            if "version" in data and "number" in data["version"]:
                version = data["version"]["number"]
                cluster_name = data.get("cluster_name", "default")
                return {
                    "success": True,
                    "message": f"Successfully connected to Elastic {version} (Cluster: {cluster_name})",
                    "details": {
                        "version": version,
                        "cluster_name": cluster_name,
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
            logger.error(f"Elastic connection test failed: {str(e)}")
            return {
                "success": False,
                "message": f"Connection failed: {str(e)}",
                "details": {
                    "error_type": type(e).__name__,
                    "api_endpoint": self.api_url
                }
            }
