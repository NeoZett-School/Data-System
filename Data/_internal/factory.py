from typing import TypeVar, Optional, Any, Type
from .data import Data

T = TypeVar("T", bound=Data)

class _Dataclass(Data):
    __slots__ = ("content", "annotations",)
    def __init__(self, **kwargs: Any) -> None:
        cls = self.__class__
        class_fields = {
            k: v for k, v in cls.__dict__.items()
            if not k.startswith("_") and not callable(v)
        }
        kwargs.update(class_fields)
        super().__init__(**kwargs)
        object.__setattr__(self, "annotations", dict(cls.__annotations__))
    def __repr__(self) -> str:
        fields = ', '.join(f"{key}={value!r}" for key, value in self.items() if key.startswith("_") is False and not callable(value))
        return f"{self.__class__.__name__}({fields})"
    def __str__(self) -> str:
        return self.__repr__()

def data_factory(cls: Optional[Type[T]] = None, /, frozen: bool = False, include_methods: bool = False, **kwargs: Any) -> Type[T]:
    """
    Converts a standard class into a Data-like class.

    For correct typing, you must inherit from Data in the class definition.

    Set `include_methods=True` in kwargs to include methods as fields.
    """
    is_decorator = not cls is None and not kwargs

    def decorator(cls: Type[T]) -> Type[T]:
        if not isinstance(cls, type):
            raise TypeError("The argument must be a class. This is required to convert into a dataclass.")
        
        namespace = dict(cls.__dict__)
        namespace["__module__"] = cls.__module__
        namespace["__qualname__"] = cls.__qualname__

        config = getattr(cls, "__meta_config__", {})
        config.update(kwargs)

        return type(cls.__name__, (_Dataclass,), namespace, frozen=frozen, include_methods=include_methods, **config)
    
    if not is_decorator:
        return decorator
    
    return decorator(cls)