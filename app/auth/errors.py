from core.errors import ApplicationError


class AuthError(ApplicationError):
    """
    PURPOSE: Base exception class for all authentication-related errors
    DESCRIPTION: Root exception type for authentication domain errors, inheriting from ApplicationError
                 to integrate with the application's error handling system.
    """
    pass


class NotAuthorizedError(AuthError):
    """
    PURPOSE: Exception raised when user authorization fails or is missing
    DESCRIPTION: Indicates that the user lacks valid authentication credentials or the provided
                 credentials are invalid, expired, or malformed.
    """
    pass


class InvalidLoginOrPasswordError(AuthError):
    """
    PURPOSE: Exception raised when login credentials are incorrect
    DESCRIPTION: Indicates that the provided username does not exist or the password
                 does not match the stored hash for the user.
    """
    pass


class RefreshTokenRequiredError(AuthError):
    """
    PURPOSE: Exception raised when refresh token is missing for token renewal
    DESCRIPTION: Indicates that a refresh token operation was attempted without providing
                 the required refresh token.
    """
    pass


class AdminRightsRequiredError(AuthError):
    """
    PURPOSE: Exception raised when administrative privileges are required but not present
    DESCRIPTION: Indicates that the authenticated user lacks the necessary administrative
                 permissions to perform the requested operation.
    """
    pass
