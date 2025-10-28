"""A flexible data container class that behaves like both a dictionary and an object with attributes."""

from typing import (
    Iterable, Set, Tuple, List, Dict, Any, Optional, Type, TypeVar, Generic, 
    Literal, overload, KeysView, ValuesView, ItemsView, Union, 
    FrozenSet, get_origin, get_args
)
from .meta import DataMeta

V = TypeVar("V")
DictSchema = Dict[str, V]

class Data(Generic[V], Iterable, metaclass=DataMeta):
    """A flexible data container class that behaves like both a dictionary and an object with attributes."""
    annotations: Dict[str, Type]
    content: DictSchema

    __frozen__: bool
    __include_methods__: bool
    __meta_config__: Dict[str, Any]
    __slots__ = ("content", "annotations", "__frozen__", "__include_methods__", "__meta_config__", "__original__", "__was_frozen__",) # __weakref__ is already defined in generic

    def __init__(self, value: Optional[DictSchema] = None, frozen: bool = False, include_methods: bool = False, **kwargs: Any) -> None:
        """Initializes the Data object with optional dictionary content and keyword arguments."""

        instance_content = dict()
        instance_content.update(value or {})
        instance_content.update(kwargs) # Overwrite with instance-level arguments
        object.__setattr__(self, "annotations", {})
        object.__setattr__(self, "content", instance_content)
        object.__setattr__(self, "__frozen__", frozen or self.meta.get("frozen", False))
        object.__setattr__(self, "__include_methods__", include_methods or self.meta.get("include_methods", False))
        try:
            object.__setattr__(self, "__meta_config__", dict(object.__getattribute__(self, "__class__").__meta_config__))
        except AttributeError: pass # Then the "__meta_config__" is most likely read-only, when we don't use "data_factory"
        self.__raise_typing_error__()
    
    @property
    def meta(self) -> Dict[str, Any]:
        """Allocate and retrieve relevant metadata for the Data object."""
        cls_meta = object.__getattribute__(self, "__class__").__meta_config__ or {}
        instance_meta = object.__getattribute__(self, "content").get("__meta_config__", {})
        merged_meta = {}
        merged_meta.update(cls_meta)
        merged_meta.update(instance_meta)
        return merged_meta
    
    def __check_type(self, value: Any, annotation: Type) -> bool:
        """Recursively checks if a value conforms to a given typing annotation."""
        origin = get_origin(annotation)
        args = get_args(annotation)

        if origin is None:
            if annotation in (Any, TypeVar): 
                return True
            if value is None and annotation is type(None):
                return True
            try:
                return isinstance(value, annotation)
            except TypeError:
                return True 
            
        if origin is Union:
            return any(self.__check_type(value, arg) for arg in args)

        if origin in (tuple, Tuple, list, List, dict, Dict, set, Set, frozenset, FrozenSet):
            if not isinstance(value, origin):
                return False

            if origin in (list, List, set, Set, frozenset, FrozenSet) and args:
                item_type = args[0]
                return all(self.__check_type(item, item_type) for item in value)
            
            if origin in (tuple, Tuple) and args:
                return all(self.__check_type(value[i], args[i]) if len(value) > i < len(args) else True for i in range(len(value)))

            if origin in (dict, Dict) and len(args) == 2:
                key_type, value_type = args
                return all(self.__check_type(k, key_type) and self.__check_type(v, value_type)
                           for k, v in value.items())
        
        if not isinstance(value, origin):
            return False
            
        return True

    def __get_incorrect_typing__(self, annotations: Optional[Dict[str, Type]] = None) -> List[str]:
        annotations = annotations or object.__getattribute__(self, "annotations")
        if not annotations:
            return []
            
        incorrect: List[str] = []
        content = object.__getattribute__(self, "content")
        
        for k, annotation in annotations.items():
            if k not in content:
                continue 

            value = content[k]
            if not self.__check_type(value, annotation):
                incorrect.append(k)

        return incorrect
    
    def __raise_typing_error__(self) -> None:
        annotations = object.__getattribute__(self, "annotations")
        if not annotations:
            return
        incorrect = self.__get_incorrect_typing__(annotations)
        if incorrect:
            raise TypeError(f"Incorrect typing for fields: {', '.join(incorrect)}")
    
    def copy(self) -> "Data[V]":
        """Creates a shallow copy of the Data object."""
        return type(self)(object.__getattribute__(self, "content").copy())
    
    @classmethod
    def from_dict(cls: Type["Data[V]"], data: DictSchema) -> "Data[V]":
        """Creates a Data object from a dictionary."""
        return cls(data)
    
    def to_dict(self) -> Union[DictSchema, FrozenSet]:
        """Converts the Data object to a standard dictionary."""
        content = dict(object.__getattribute__(self, "content"))
        if object.__getattribute__(self, "__frozen__"):
            return frozenset(content)
        return content
    
    def keys(self) -> KeysView[str]:
        """Return a set-like object providing a view on the data's keys."""
        return object.__getattribute__(self, "content").keys()
    def values(self) -> ValuesView[V]:
        """Return a set-like object providing a view on the data's values."""
        return object.__getattribute__(self, "content").values()
    def items(self) -> ItemsView[str, V]:
        """Return a set-like object providing a view on the data's items."""
        return object.__getattribute__(self, "content").items()
    
    @overload
    def get(self, key: str, default: Literal[None] = None) -> Optional[V]: ...
    @overload
    def get(self, key: str, default: V) -> V: ...
    def get(self, key: str, default: Optional[V] = None) -> Optional[V]:
        """Return the value for key if key is in the dictionary, else default."""
        return object.__getattribute__(self, "content").get(key, default)
    
    @overload
    def setdefault(self, key: str, default: Literal[None] = None) -> Optional[V]: ...
    @overload
    def setdefault(self, key: str, default: V) -> V: ...
    def setdefault(self, key: str, default: Optional[V] = None) -> Optional[V]:
        if object.__getattribute__(self, "__frozen__"):
            return object.__getattribute__(self, "content").get(key, default)
        result = object.__getattribute__(self, "content").setdefault(key, default)
        self.__raise_typing_error__()
        return result
    
    @overload
    def pop(self, key: str, default: Literal[None] = None) -> Optional[V]: ...
    @overload
    def pop(self, key: str, default: V) -> V: ...
    def pop(self, key: str, default: Optional[V] = None) -> Optional[V]:
        """
        D.pop(k[,d]) -> v, remove specified key and return the corresponding value.

        If the key is not found, return the default if given; otherwise,
        raise a KeyError.
        """
        if object.__getattribute__(self, "__frozen__"):
            return object.__getattribute__(self, "content").get(key, default)
        return object.__getattribute__(self, "content").pop(key, default)
    
    def update(self, data: DictSchema) -> None:
        if object.__getattribute__(self, "__frozen__"):
            return
        object.__getattribute__(self, "content").update(data)
        self.__raise_typing_error__()
    
    def clear(self) -> None:
        if object.__getattribute__(self, "__frozen__"):
            return
        object.__getattribute__(self, "content").clear()
    
    def __call__(self, key: str, /, *args: Any, **kwargs: Any) -> Any:
        """Calls a callable stored in the data with the given key, passing any additional arguments."""
        return object.__getattribute__(self, "content")[key](*args, **kwargs)
    
    def __getattribute__(self, name: str) -> Any:
        # Fast path: directly handle internal attributes
        if name in {"__class__", "__dict__", "__include_methods__", "__frozen__", "__meta_config__", "content"}:
            return object.__getattribute__(self, name)

        this_cls = type(self)

        # Determine if 'name' belongs to the Data class hierarchy
        in_data = any(name in c.__dict__ for c in Data.__mro__)
        if in_data:
            return object.__getattribute__(self, name)

        # Determine if 'name' belongs to this class but not to Data
        data_keys = {k for c in Data.__mro__ for k in c.__dict__}
        this_keys = {k for c in this_cls.__mro__ for k in c.__dict__ if k not in data_keys}

        if name in this_keys and object.__getattribute__(self, "__include_methods__"):
            return object.__getattribute__(self, name)

        # Try to retrieve from 'content'
        content = object.__getattribute__(self, "content")
        if name in content:
            return content[name]

        # Otherwise, standard Python AttributeError
        raise AttributeError(f"'{this_cls.__name__}' object has no attribute '{name}'")
    
    def __setattr__(self, name: str, value: Any) -> None:
        if object.__getattribute__(self, "__frozen__"):
            return
        object.__getattribute__(self, "content")[name] = value
        self.__raise_typing_error__()
    
    def __enter__(self) -> "Data":
        object.__setattr__(self, "__original__", object.__getattribute__(self, "content").copy())
        object.__setattr__(self, "__was_frozen__", object.__getattribute__(self, "__frozen__"))
        object.__setattr__(self, "__frozen__", False)
        return self
    
    def __exit__(self, *args: Any) -> None:
        if any(args):
            object.__setattr__(self, "content", object.__getattribute__(self, "__original__"))
        object.__setattr__(self, "__frozen__", object.__getattribute__(self, "__was_frozen__"))
    
    def __getitem__(self, key: str) -> V:
        return object.__getattribute__(self, "content")[key]
    def __setitem__(self, key: str, value: V) -> None:
        if object.__getattribute__(self, "__frozen__"):
            return
        object.__getattribute__(self, "content")[key] = value
        self.__raise_typing_error__()
    def __delitem__(self, key: str) -> None:
        if object.__getattribute__(self, "__frozen__"):
            return
        del object.__getattribute__(self, "content")[key]
    def __contains__(self, key: str) -> bool:
        return key in object.__getattribute__(self, "content")
    def __eq__(self, other: Union[Any, "Data"]) -> bool:
        if isinstance(other, Data):
            return (object.__getattribute__(self, "content") == 
                    object.__getattribute__(other, "content"))
        if isinstance(other, dict):
            return object.__getattribute__(self, "content") == other
        return NotImplemented
    def __iter__(self):
        return iter(object.__getattribute__(self, "content"))
    def __len__(self) -> int:
        return len(object.__getattribute__(self, "content"))
    def __repr__(self) -> str:
        items = ", ".join(f"{k}={v!r}" for k, v in self.items() if not k.startswith("_") and not callable(v))
        return f"{type(self).__name__}({items})" if items else f"{type(self).__name__}()"
    def __str__(self) -> str:
        return str(object.__getattribute__(self, "content"))
    def __hash__(self) -> int:
        return hash(frozenset(object.__getattribute__(self, "content").items()))