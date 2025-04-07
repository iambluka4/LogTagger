class SIEMException(Exception):
    """Base exception for all SIEM-related errors"""
    pass

class SIEMConnectionError(SIEMException):
    """Error when connecting to SIEM"""
    def __init__(self, siem_type, url, message=None):
        self.siem_type = siem_type
        self.url = url
        self.message = message or f"Failed to connect to {siem_type} at {url}"
        super().__init__(self.message)

class SIEMAuthenticationError(SIEMException):
    """Authentication error with SIEM"""
    def __init__(self, siem_type, message=None):
        self.siem_type = siem_type
        self.message = message or f"Authentication failed for {siem_type}"
        super().__init__(self.message)

class SIEMRateLimitError(SIEMException):
    """Rate limit or quota exceeded"""
    def __init__(self, siem_type, message=None):
        self.siem_type = siem_type
        self.message = message or f"Rate limit exceeded for {siem_type}"
        super().__init__(self.message)

class SIEMResponseError(SIEMException):
    """Error in response from SIEM"""
    def __init__(self, siem_type, status_code=None, message=None):
        self.siem_type = siem_type
        self.status_code = status_code
        status_info = f" (Status code: {status_code})" if status_code else ""
        self.message = message or f"Invalid response from {siem_type}{status_info}"
        super().__init__(self.message)
