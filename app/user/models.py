import uuid
from dataclasses import dataclass, field
from uuid import UUID

from core.models import Model


@dataclass(kw_only=True)
class User(Model):
    id: UUID = field(default_factory=uuid.uuid4)
    username: str
