import uuid
from dataclasses import dataclass, field
from uuid import UUID

from core.models import Model


@dataclass(kw_only=True)
class Auth(Model):
    id: UUID = field(default_factory=uuid.uuid4)
    user_id: UUID
    username: str
    password_hash: str
    is_admin: bool = False
