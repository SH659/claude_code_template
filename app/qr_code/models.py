import uuid
from dataclasses import dataclass, field
from uuid import UUID

import qrcode
from PIL import Image

from core.models import Model
from core.settings import settings


@dataclass(kw_only=True)
class QrCode(Model):
    """
    PURPOSE: Domain model representing QR code entities with image generation capabilities
    DESCRIPTION: Contains QR code information including user ownership, descriptive name, and target link.
                 Provides functionality to generate QR code images that redirect to configured endpoints.
    ATTRIBUTES:
        id: UUID - Unique identifier for the QR code
        user_id: UUID - Reference to the owning user entity
        name: str - Descriptive name for the QR code
        link: str - Target URL that the QR code redirects to
    """
    id: UUID = field(default_factory=uuid.uuid4)
    user_id: UUID
    name: str
    link: str

    def get_image(self) -> Image.Image:
        """
        PURPOSE: Generate PIL Image containing QR code for this record
        DESCRIPTION: Creates a QR code image that encodes a URL pointing to the application's
                     QR code endpoint with this record's ID. The generated QR code redirects
                     to the configured API endpoint when scanned.
        RETURNS: Image.Image - PIL Image object containing the generated QR code
        CONTRACTS:
            POSTCONDITION:
                - QR code encodes URL with pattern: http://{API_URL}{QR_CODE_ENDPOINT}
                - QR code uses medium error correction level
                - Image has black foreground on white background
        """
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
