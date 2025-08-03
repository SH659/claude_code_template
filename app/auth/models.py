import uuid
from dataclasses import dataclass, field
from uuid import UUID

from core.models import Model


@dataclass(kw_only=True)
class Auth(Model):
    """
    PURPOSE: Domain model representing user authentication credentials and permissions
    DESCRIPTION: Contains user authentication information including hashed password and admin status.
                 Inherits from Model to get automatic exception generation and validation capabilities.
    ATTRIBUTES:
        id: UUID - Unique identifier for the authentication record
        user_id: UUID - Reference to the associated user entity
        username: str - Unique username for authentication
        password_hash: str - Bcrypt hashed password for secure storage
        is_admin: bool - Flag indicating administrative privileges, defaults to False
    """
    id: UUID = field(default_factory=uuid.uuid4)
    user_id: UUID
    username: str
    password_hash: str
    is_admin: bool = False
