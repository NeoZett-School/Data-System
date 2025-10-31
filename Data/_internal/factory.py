from typing import TypeVar, Optional, Any, Type
from .data import Data

T = TypeVar("T", bound=Data)

class _Dataclass(Data):
    
    __slots__ = Data.__slots__ + ("__weakref__",)

    def __init__(self, **kwargs: Any) -> None:
        cls = type(self)

        instance_content = {}
        for base in reversed(cls.__mro__):
            base_dict = getattr(base, '__dict__', {})
            for k, v in base_dict.items():
                if (
                    not k.startswith("_")
                    and not callable(v)
                    and k not in {"annotations", "content"}
                ):
                    instance_content[k] = v

        instance_content.update(kwargs)

        super().__init__(value=instance_content)

        anns: dict[str, Any] = {}
        for base in reversed(cls.__mro__):
            anns.update(getattr(base, "__annotations__", {}))

        object.__setattr__(self, "annotations", anns)
        self.__raise_typing_error__()

def data_factory(
    cls: Optional[Type[T]] = None, /,
    frozen: bool = False,
    include_methods: bool = False,
    **kwargs: Any
) -> Type[T]:
    """
    Converts a standard class into a Data-like class.

    Inherits existing bases and annotations safely.
    """

    def decorator(cls: Type[T]) -> Type[T]:
        if not isinstance(cls, type):
            raise TypeError("data_factory can only decorate a class.")

        # Preserve original bases (unless Data or _Dataclass missing)
        bases = tuple(b for b in cls.__bases__ if b not in (object,))
        if not any(issubclass(base, Data) for base in bases):
            bases = (_Dataclass,) + bases

        namespace = dict(cls.__dict__)
        namespace["__module__"] = cls.__module__
        namespace["__qualname__"] = cls.__qualname__

        config = getattr(cls, "__meta_config__", {}).copy()
        config.update(kwargs)

        new_cls = type(
            cls.__name__,
            bases,
            namespace,
            frozen=frozen,
            include_methods=include_methods,
            **config
        )
        return new_cls

    return decorator if cls is None else decorator(cls)