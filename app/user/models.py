import uuid
from dataclasses import dataclass, field
from uuid import UUID

from core.models import Model


@dataclass(kw_only=True)
class User(Model):
    """
    PURPOSE: Domain model representing user account information
    DESCRIPTION: Contains basic user account data including unique identifier and username.
                 Inherits from Model to get automatic exception generation capabilities.
    ATTRIBUTES:
        id: UUID - Unique identifier for the user account
        username: str - Unique username for the user
    """
    id: UUID = field(default_factory=uuid.uuid4)
    username: str
