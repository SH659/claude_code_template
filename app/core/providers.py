from dishka import Provider, Scope, provide

from core.serializer import DataclassSerializer, Serializer
from core.types import DTO


class DataclassSerializerProvider(Provider):
    """
    PURPOSE: Dependency injection provider for dataclass serialization
    DESCRIPTION: Dishka provider that creates and provides DataclassSerializer instances
    for converting between domain models and DTOs. Uses generic type parameters to
    ensure type safety during serialization operations.
    """
    @provide(scope=Scope.APP)
    def serializer[T](self, model: type[T]) -> Serializer[T, DTO]:
        """
        PURPOSE: Create and provide typed serializer for dataclass models
        DESCRIPTION: Creates a DataclassSerializer instance configured for the specified
        model type, providing type-safe serialization between domain models and DTOs.
        ARGUMENTS:
            model: type[T] - Domain model class type for serialization
        RETURNS: Serializer[T, DTO] - Configured serializer for the model type
        """
        return DataclassSerializer(model)
