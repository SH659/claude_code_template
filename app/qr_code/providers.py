from dishka import Provider, Scope, provide

from qr_code.dal import QrCodeCrud, QrCodeRepo
from qr_code.services import QrCodeService


class QrCodeProvider(Provider):
    crud = provide(QrCodeCrud, scope=Scope.REQUEST)
    repo = provide(QrCodeRepo, scope=Scope.REQUEST)
    service = provide(QrCodeService, scope=Scope.REQUEST)
