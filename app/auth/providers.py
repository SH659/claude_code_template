from dishka import Provider, Scope, provide

from auth.dal import AuthCrud, AuthRepo
from auth.services import AuthService


class AuthProvider(Provider):
    """
    PURPOSE: Dishka dependency injection provider for authentication components
    DESCRIPTION: Configures dependency injection for authentication layer including CRUD operations,
                 repository pattern implementation, and service layer components. All dependencies
                 are scoped to REQUEST lifetime for proper resource management.
    ATTRIBUTES:
        crud: AuthCrud - Provides AuthCrud instances with REQUEST scope
        repo: AuthRepo - Provides AuthRepo instances with REQUEST scope
        service: AuthService - Provides AuthService instances with REQUEST scope
    """
    crud = provide(AuthCrud, scope=Scope.REQUEST)
    repo = provide(AuthRepo, scope=Scope.REQUEST)
    service = provide(AuthService, scope=Scope.REQUEST)
