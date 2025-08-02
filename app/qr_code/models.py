import uuid
from dataclasses import dataclass, field
from uuid import UUID

import qrcode
from PIL import Image

from core.models import Model
from core.settings import settings


@dataclass(kw_only=True)
class QrCode(Model):
    id: UUID = field(default_factory=uuid.uuid4)
    user_id: UUID
    name: str
    link: str

    def get_image(self) -> Image.Image:
        qr = qrcode.main.QRCode(
            version=5,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data("http://" + settings.API_URL + settings.QR_CODE_ENDPOINT.format(uuid=self.id))
        qr.make(fit=True)
        img = qr.make_image(fill="black", back_color="white")
        return img
