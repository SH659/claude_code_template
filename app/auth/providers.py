from dishka import Provider, Scope, provide

from auth.dal import AuthCrud, AuthRepo
from auth.services import AuthService


class AuthProvider(Provider):
    crud = provide(AuthCrud, scope=Scope.REQUEST)
    repo = provide(AuthRepo, scope=Scope.REQUEST)
    service = provide(AuthService, scope=Scope.REQUEST)
