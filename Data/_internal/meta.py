from typing import Dict, Any, Type
from abc import ABCMeta

__all__ = ("DataMeta",)

class DataMeta(ABCMeta):
    """Metaclass to process configuration arguments at class definition time."""
    __meta_config__: Dict[str, Any]
    def __new__(mcs, name: str, bases: tuple[Type, ...], namespace: Dict[str, Any], **kwargs: Any) -> Type:
        new_cls = super().__new__(mcs, name, bases, namespace)
        new_cls.__meta_config__ = dict(kwargs)
        return new_cls