class OddjobError(Exception):
    """Base exception for oddjob-related errors."""


class OddjobGenerateResultTokenError(OddjobError):
    def __init__(self):
        super().__init__("Failed to generate oddjob result token.")


class OddjobPublishResultError(OddjobError):
    def __init__(self):
        super().__init__("Failed to publish oddjob result.")


class OddjobGetResultError(OddjobError):
    def __init__(self):
        super().__init__("Failed to get oddjob result.")


class OddjobAuthorizationError(OddjobError):
    def __init__(self):
        super().__init__("User is not authorized to access this oddjob task result.")


class OddjobInvalidResultTokenError(OddjobError):
    def __init__(self):
        super().__init__("The provided oddjob result token is invalid.")
