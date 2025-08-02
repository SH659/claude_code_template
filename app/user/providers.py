from dishka import Provider, Scope, provide

from user.dal import UserCrud, UserRepo
from user.services import UserService


class UserProvider(Provider):
    crud = provide(UserCrud, scope=Scope.REQUEST)
    repo = provide(UserRepo, scope=Scope.REQUEST)
    service = provide(UserService, scope=Scope.REQUEST)
