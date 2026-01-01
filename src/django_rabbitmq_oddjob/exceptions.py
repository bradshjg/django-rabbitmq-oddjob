class OddjobException(Exception):
    """Base exception for oddjob-related errors."""
    pass

class OddjobAuthorizationError(OddjobException):
    """Raised when a user is not authorized to access an oddjob task result."""
    def __init__(self, message="User is not authorized to access this oddjob task result."):
        super().__init__(message)

class OddjobInvalidResultTokenError(OddjobException):
    """Raised when an oddjob task result is not found."""
    def __init__(self, message="The provided oddjob result token is invalid."):
        super().__init__(message)
