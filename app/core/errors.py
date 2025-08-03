class ApplicationError(Exception):
    """
    PURPOSE: Base exception class for all application-specific errors
    DESCRIPTION: Root exception type that serves as the parent for all custom
    application exceptions, enabling unified exception handling patterns.
    """
    pass


class NotFoundError(ApplicationError):
    """
    PURPOSE: Exception for resource not found errors
    DESCRIPTION: Raised when requested resources cannot be located in the system.
    Provides contextual error messages based on the resource type.
    """
    def __init__(self, resource: str = "Resource"):
        """
        PURPOSE: Initialize not found error with resource context
        DESCRIPTION: Creates a NotFoundError with a descriptive message
        indicating which type of resource was not found.
        ARGUMENTS:
            resource: str - Name of the resource that was not found
        """
        super().__init__(f"{resource} not found")


class AlreadyExistError(ApplicationError):
    """
    PURPOSE: Exception for resource already exists errors
    DESCRIPTION: Raised when attempting to create resources that already exist
    in the system. Provides contextual error messages based on the resource type.
    """
    def __init__(self, resource: str = "Resource"):
        """
        PURPOSE: Initialize already exists error with resource context
        DESCRIPTION: Creates an AlreadyExistError with a descriptive message
        indicating which type of resource already exists.
        ARGUMENTS:
            resource: str - Name of the resource that already exists
        """
        super().__init__(f"{resource} already exists")
