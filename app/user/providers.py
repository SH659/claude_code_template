from dishka import Provider, Scope, provide

from user.dal import UserCrud, UserRepo
from user.services import UserService


class UserProvider(Provider):
    """
    PURPOSE: Dishka dependency injection provider for user management components
    DESCRIPTION: Configures dependency injection for user management layer including CRUD operations,
                 repository pattern implementation, and service layer components. All dependencies
                 are scoped to REQUEST lifetime for proper resource management.
    ATTRIBUTES:
        crud: UserCrud - Provides UserCrud instances with REQUEST scope
        repo: UserRepo - Provides UserRepo instances with REQUEST scope
        service: UserService - Provides UserService instances with REQUEST scope
    """
    crud = provide(UserCrud, scope=Scope.REQUEST)
    repo = provide(UserRepo, scope=Scope.REQUEST)
    service = provide(UserService, scope=Scope.REQUEST)
