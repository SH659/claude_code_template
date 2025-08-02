from typing import ClassVar, Type

from core import errors


class Model:
    NotFoundError: ClassVar[Type[errors.NotFoundError]]
    AlreadyExistError: ClassVar[Type[errors.AlreadyExistError]]

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        class NotFoundError(errors.NotFoundError):
            def __init__(self):
                super().__init__(cls.__name__)

            __qualname__ = f"{cls.__qualname__}.NotFoundError"

        cls.NotFoundError = NotFoundError

        class AlreadyExistError(errors.AlreadyExistError):
            def __init__(self):
                super().__init__(cls.__name__)

            __qualname__ = f"{cls.__qualname__}.AlreadyExistError"  # Fix traceback name

        cls.AlreadyExistError = AlreadyExistError
