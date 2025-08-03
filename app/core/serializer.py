from __future__ import annotations

import dataclasses
from abc import ABC, abstractmethod
from dataclasses import is_dataclass
from typing import Protocol, Sequence

from core.types import DTO


class Serializer[Model, DTO](Protocol):
    """
    PURPOSE: Protocol interface for object serialization between domain models and DTOs
    DESCRIPTION: Type protocol that defines the contract for serialization components,
    providing bidirectional conversion between domain models and data transfer objects
    with support for batch operations through flat property.
    """
    def serialize(self, obj: Model) -> DTO:
        """
        PURPOSE: Convert domain model to data transfer object
        DESCRIPTION: Serializes a domain model instance into a DTO format
        suitable for database operations or API responses.
        ARGUMENTS:
            obj: Model - Domain model instance to serialize
        RETURNS: DTO - Serialized data transfer object
        """
        pass

    def deserialize(self, obj: DTO) -> Model:
        """
        PURPOSE: Convert data transfer object to domain model
        DESCRIPTION: Deserializes a DTO into a domain model instance
        for business logic operations.
        ARGUMENTS:
            obj: DTO - Data transfer object to deserialize
        RETURNS: Model - Deserialized domain model instance
        """
        pass

    @property
    def flat(self) -> Serializer[Sequence[Model], Sequence[DTO]]:
        """
        PURPOSE: Get batch serializer for collections of objects
        DESCRIPTION: Returns a serializer instance configured for batch operations
        on sequences of models and DTOs.
        RETURNS: Serializer[Sequence[Model], Sequence[DTO]] - Batch serializer
        """
        pass


class SerializerBase[Model, DTO](ABC, Serializer[Model, DTO]):
    """
    PURPOSE: Abstract base implementation for serializer protocol
    DESCRIPTION: Provides common serializer functionality including flat property
    implementation while enforcing abstract methods for concrete serialization logic.
    """
    @abstractmethod
    def serialize(self, obj: Model) -> DTO:
        """
        PURPOSE: Convert domain model to DTO representation
        DESCRIPTION: Abstract method that must be implemented by concrete serializers to transform
                     domain model instances into DTO format suitable for database operations.
        ARGUMENTS:
            obj: Model - Domain model instance to serialize
        RETURNS: DTO - Data Transfer Object representation of the model
        """
        pass

    @abstractmethod
    def deserialize(self, obj: DTO) -> Model:
        """
        PURPOSE: Convert DTO representation to domain model
        DESCRIPTION: Abstract method that must be implemented by concrete serializers to transform
                     DTO data into domain model instances for business logic operations.
        ARGUMENTS:
            obj: DTO - Data Transfer Object to deserialize
        RETURNS: Model - Domain model instance created from DTO data
        """
        pass

    @property
    def flat(self) -> Serializer[Sequence[Model], Sequence[DTO]]:
        """
        PURPOSE: Create batch serializer using this serializer for individual items
        DESCRIPTION: Returns a FlatSerializer instance that uses this serializer
        for individual item serialization in batch operations.
        RETURNS: Serializer[Sequence[Model], Sequence[DTO]] - Flat serializer wrapper
        """
        return FlatSerializer(self)


class FlatSerializer[Model, DTO](SerializerBase[Sequence[Model], Sequence[DTO]]):
    """
    PURPOSE: Batch serializer for collections of objects
    DESCRIPTION: Wrapper serializer that applies single-item serialization logic
    to sequences of models and DTOs, enabling efficient batch operations.
    ATTRIBUTES:
        serializer: Serializer[Model, DTO] - Single-item serializer instance
    """
    def __init__(self, serializer: Serializer[Model, DTO]):
        """
        PURPOSE: Initialize flat serializer with single-item serializer
        DESCRIPTION: Sets up the batch serializer with a single-item serializer
        that will be used for each element in collections.
        ARGUMENTS:
            serializer: Serializer[Model, DTO] - Single-item serializer
        """
        self.serializer = serializer

    def serialize(self, objs: Sequence[Model]) -> Sequence[DTO]:
        """
        PURPOSE: Serialize a sequence of domain models to DTOs
        DESCRIPTION: Applies single-item serialization to each model in the sequence.
        ARGUMENTS:
            objs: Sequence[Model] - Collection of domain models to serialize
        RETURNS: Sequence[DTO] - Collection of serialized DTOs
        """
        return [self.serializer.serialize(obj) for obj in objs]

    def deserialize(self, objs: Sequence[DTO]) -> Sequence[Model]:
        """
        PURPOSE: Deserialize a sequence of DTOs to domain models
        DESCRIPTION: Applies single-item deserialization to each DTO in the sequence.
        ARGUMENTS:
            objs: Sequence[DTO] - Collection of DTOs to deserialize
        RETURNS: Sequence[Model] - Collection of deserialized domain models
        """
        return [self.serializer.deserialize(obj) for obj in objs]


class DataclassSerializer[Model, T_DTO: DTO](SerializerBase[Model, T_DTO]):
    """
    PURPOSE: Serializer implementation for dataclass domain models
    DESCRIPTION: Concrete serializer that converts between dataclass models and
    dictionary DTOs using dataclasses.asdict and constructor instantiation.
    ATTRIBUTES:
        model: type[Model] - Dataclass model type for deserialization
    """
    def __init__(self, model: type[Model]):
        """
        PURPOSE: Initialize serializer with dataclass model type
        DESCRIPTION: Sets up the serializer with the target dataclass model type
        and validates that the provided model is indeed a dataclass.
        ARGUMENTS:
            model: type[Model] - Dataclass model type for serialization
        CONTRACTS:
            PRECONDITION:
                - model is a type object
                - model is decorated with @dataclass
            RAISES:
                - TypeError - when model is not a dataclass type
        """
        self.model = model
        if not isinstance(model, type) or not is_dataclass(model):
            raise TypeError(f"Argument 'model' must be a dataclass class. Got '{model}'.")

    def serialize(self, obj: Model) -> DTO:
        """
        PURPOSE: Convert dataclass model to dictionary DTO
        DESCRIPTION: Uses dataclasses.asdict to convert the dataclass instance
        into a dictionary representation suitable for database operations.
        ARGUMENTS:
            obj: Model - Dataclass model instance to serialize
        RETURNS: DTO - Dictionary representation of the model
        """
        return dataclasses.asdict(obj)

    def deserialize(self, obj: DTO) -> Model:
        """
        PURPOSE: Convert dictionary DTO to dataclass model
        DESCRIPTION: Creates a new dataclass instance by unpacking the DTO
        dictionary as constructor arguments.
        ARGUMENTS:
            obj: DTO - Dictionary data to deserialize
        RETURNS: Model - New dataclass model instance
        CONTRACTS:
            PRECONDITION:
                - obj contains all required fields for model constructor
            RAISES:
                - TypeError - when obj contains invalid field names or values
        """
        return self.model(**obj)
