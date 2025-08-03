from dishka import Provider, Scope, provide

from qr_code.dal import QrCodeCrud, QrCodeRepo
from qr_code.services import QrCodeService


class QrCodeProvider(Provider):
    """
    PURPOSE: Dishka dependency injection provider for QR code management components
    DESCRIPTION: Configures dependency injection for QR code management layer including CRUD operations,
                 repository pattern implementation, and service layer components. All dependencies
                 are scoped to REQUEST lifetime for proper resource management.
    ATTRIBUTES:
        crud: QrCodeCrud - Provides QrCodeCrud instances with REQUEST scope
        repo: QrCodeRepo - Provides QrCodeRepo instances with REQUEST scope
        service: QrCodeService - Provides QrCodeService instances with REQUEST scope
    """
    crud = provide(QrCodeCrud, scope=Scope.REQUEST)
    repo = provide(QrCodeRepo, scope=Scope.REQUEST)
    service = provide(QrCodeService, scope=Scope.REQUEST)
