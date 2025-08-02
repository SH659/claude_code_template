from dishka import Provider, Scope, provide

from core.serializer import DataclassSerializer, Serializer
from core.types import DTO


class DataclassSerializerProvider(Provider):
    @provide(scope=Scope.APP)
    def serializer[T](self, model: type[T]) -> Serializer[T, DTO]:
        return DataclassSerializer(model)
