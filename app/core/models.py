from typing import ClassVar, Type

from core import errors


class Model:
    """
    PURPOSE: Base class for domain models that provides model-specific exception classes
    DESCRIPTION: Abstract base class that automatically generates custom NotFoundError and AlreadyExistError
    exception classes for each subclass. Uses __init_subclass__ to dynamically create nested exception
    classes that include the model name in their error messages, enabling more descriptive error handling
    throughout the application. Each subclass gets its own exception types accessible as class attributes.
    """
    NotFoundError: ClassVar[Type[errors.NotFoundError]]
    AlreadyExistError: ClassVar[Type[errors.AlreadyExistError]]

    def __init_subclass__(cls, **kwargs):
        """
        PURPOSE: Automatically creates model-specific exception classes for each subclass
        DESCRIPTION: Hook method called when a class is subclassed. Creates two nested exception classes
        (NotFoundError and AlreadyExistError) that inherit from the core error types but include the
        model class name in their error messages. Sets proper __qualname__ for better tracebacks.
        ARGUMENTS:
            cls: type - The subclass being created
            **kwargs: dict - Additional keyword arguments passed to super().__init_subclass__
        RETURNS: None
        CONTRACTS:
            POSTCONDITION:
                - cls.NotFoundError is a subclass of errors.NotFoundError
                - cls.AlreadyExistError is a subclass of errors.AlreadyExistError
                - Both exception classes have proper __qualname__ set for tracebacks
                - Exception messages include the model class name
        """
        super().__init_subclass__(**kwargs)

        class NotFoundError(errors.NotFoundError):
            """
            PURPOSE: Model-specific NotFoundError exception with contextual error message
            DESCRIPTION: Custom exception that inherits from core NotFoundError but includes
            the specific model class name in the error message for better error context.
            """
            def __init__(self):
                """
                PURPOSE: Initialize exception with model-specific error message
                DESCRIPTION: Creates a NotFoundError with the model class name included in the message
                by passing cls.__name__ to the parent constructor.
                RETURNS: None
                CONTRACTS:
                    POSTCONDITION:
                        - Exception message contains the model class name
                """
                super().__init__(cls.__name__)

            __qualname__ = f"{cls.__qualname__}.NotFoundError"

        cls.NotFoundError = NotFoundError

        class AlreadyExistError(errors.AlreadyExistError):
            """
            PURPOSE: Model-specific AlreadyExistError exception with contextual error message
            DESCRIPTION: Custom exception that inherits from core AlreadyExistError but includes
            the specific model class name in the error message for better error context.
            """
            def __init__(self):
                """
                PURPOSE: Initialize exception with model-specific error message
                DESCRIPTION: Creates an AlreadyExistError with the model class name included in the message
                by passing cls.__name__ to the parent constructor.
                RETURNS: None
                CONTRACTS:
                    POSTCONDITION:
                        - Exception message contains the model class name
                """
                super().__init__(cls.__name__)

            __qualname__ = f"{cls.__qualname__}.AlreadyExistError"  # Fix traceback name

        cls.AlreadyExistError = AlreadyExistError
