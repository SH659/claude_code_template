class ApplicationError(Exception):
    pass


class NotFoundError(ApplicationError):
    def __init__(self, resource: str = "Resource"):
        super().__init__(f"{resource} not found")


class AlreadyExistError(ApplicationError):
    def __init__(self, resource: str = "Resource"):
        super().__init__(f"{resource} already exists")
