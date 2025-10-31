"""A flexible data container class that behaves like both a dictionary and an object with attributes."""

from typing import (
    Iterable, Set, Tuple, List, Dict, Any, Optional, Type, TypeVar, Generic, 
    Literal, overload, KeysView, ValuesView, ItemsView, Union, 
    FrozenSet, get_origin, get_args
)
from .fields import Field, ComputedField
from .meta import DataMeta
import os
import json

V = TypeVar("V", default=Any)
DictSchema = Dict[str, V]

class Data(Generic[V], Iterable, metaclass=DataMeta):
    """A flexible data container class that behaves like both a dictionary and an object with attributes."""
    annotations: Dict[str, Type]
    content: DictSchema

    __frozen__: bool
    __include_methods__: bool
    __auto_cast__: bool
    __meta_config__: Dict[str, Any]
    __fields__: Dict[str, Field]
    __slots__ = ("content", "annotations", "__frozen__", "__include_methods__", "__auto_cast__", "__meta_config__", "__fields__", "__original__", "__was_frozen__",) # __weakref__ is already defined in generic

    def __init__(self, value: Optional[DictSchema] = None, frozen: bool = False, include_methods: bool = False, auto_cast: bool = True, **kwargs: Any) -> None:
        """Initializes the Data object with optional dictionary content and keyword arguments."""

        instance_content = dict()
        instance_content.update(value or {})
        instance_content.update(kwargs) # Overwrite with instance-level arguments

        for k, v in instance_content.items():
            if not isinstance(v, Field):
                instance_content[k] = v
                continue
            if v.classfield: continue
            instance_content[k] = v.copy()

        object.__setattr__(self, "annotations", {})
        object.__setattr__(self, "content", instance_content)
        object.__setattr__(self, "__frozen__", frozen or self.meta.get("frozen", False))
        object.__setattr__(self, "__include_methods__", include_methods or self.meta.get("include_methods", False))
        object.__setattr__(self, "__auto_cast__", auto_cast or self.meta.get("auto_cast", False))
        object.__setattr__(self, "__fields__", {k: v for k, v in instance_content.items() if isinstance(v, Field)})
        try:
            object.__setattr__(self, "__meta_config__", dict(object.__getattribute__(self, "__class__").__meta_config__))
        except AttributeError: pass # Then the "__meta_config__" is most likely read-only, when we don't use "data_factory"

        for field in object.__getattribute__(self, "__fields__").values():
            if hasattr(field, "data"):
                field.data = self
    
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

        if isinstance(value, Field):
            field = value
            value = field.value
            if value == None:
                if field.required:
                    return False
                value = field.default

        if origin is None:
            if annotation is Any or isinstance(annotation, TypeVar): 
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
        for name, field in object.__getattribute__(self, "__fields__").items():
            if not isinstance(field, ComputedField) and not field.validator(field.value or field.default):
                incorrect.append(name)
        if incorrect:
            raise TypeError(f"Incorrect typing for fields: {', '.join(incorrect)}")
    
    def __replace_fields__(self, content: DictSchema) -> DictSchema:
        return {k: v if not isinstance(v, Field) else v.value or v.default if not isinstance(v, ComputedField) else v.value for k, v in content.items()}
    
    def __get_content__(self) -> DictSchema:
        return self.__replace_fields__(object.__getattribute__(self, "content"))
    
    def snapshot(self, version: Optional[str] = None) -> "FrozenData[V]":
        frozen = FrozenData(self.to_dict())
        frozen.__meta_config__["version"] = version or "snapshot"
        return frozen
    
    def copy(self) -> "Data[V]":
        """Creates a shallow copy of the Data object."""
        return type(self)(**object.__getattribute__(self, "content").copy())
    
    @classmethod
    def from_dict(cls: Type["Data[V]"], data: DictSchema) -> "Data[V]":
        """Creates a Data object from a dictionary."""
        return cls(data)
    
    def to_dict(self) -> Union[DictSchema, FrozenSet]:
        """Converts the Data object to a standard dictionary."""
        content = dict(self.__get_content__())
        if object.__getattribute__(self, "__frozen__"):
            return frozenset(content)
        return content

    @classmethod
    def from_json(cls, s: str) -> "Data":
        return cls.from_dict(json.loads(s))
    
    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)
    
    @classmethod
    def from_env(cls: Type["Data"], prefix: str = "") -> "Data":
        """Load Data fields from environment variables."""
        data = {}
        for k in cls.__annotations__:
            env_key = f"{prefix}{k}".upper()
            if env_key in os.environ:
                data[k] = os.environ[env_key]
        return cls(data)

    @classmethod
    def from_file(cls: Type["Data"], path: str) -> "Data":
        """Load a Data instance from a JSON file."""
        with open(path, "r") as f:
            return cls.from_dict(json.load(f))
    
    def keys(self) -> KeysView[str]:
        """Return a set-like object providing a view on the data's keys."""
        return self.__get_content__().keys()
    def values(self) -> ValuesView[V]:
        """Return a set-like object providing a view on the data's values."""
        return self.__get_content__().values()
    def items(self) -> ItemsView[str, V]:
        """Return a set-like object providing a view on the data's items."""
        return self.__get_content__().items()
    
    @overload
    def get(self, key: str, default: Literal[None] = None) -> Optional[V]: ...
    @overload
    def get(self, key: str, default: V) -> V: ...
    def get(self, key: str, default: Optional[V] = None) -> Optional[V]:
        """Return the value for key if key is in the dictionary, else default."""
        return self.__get_content__().get(key, default)
    
    @overload
    def setdefault(self, key: str, default: Literal[None] = None) -> Optional[V]: ...
    @overload
    def setdefault(self, key: str, default: V) -> V: ...
    def setdefault(self, key: str, default: Optional[V] = None) -> Optional[V]:
        if object.__getattribute__(self, "__frozen__"):
            return self.__get_content__().get(key, default)
        result = object.__getattribute__(self, "content").setdefault(key, default)
        if isinstance(result, Field):
            return result.value
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
            return self.__get_content__().get(key, default)
        if key in object.__getattribute__(self, "content"):
            result = object.__getattribute__(self, "content").pop(key, default)
            if isinstance(result, Field): return result.value
        else: return default
    
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
        value = object.__getattribute__(self, "content").get(key)
        if not callable(value): 
            raise TypeError(f"'{key}' is not callable. Are you sure you are calling this correctly?")
        return value(*args, **kwargs)
    
    def __getattribute__(self, name: str) -> V:
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
            value = object.__getattribute__(self, name)
            if callable(value): return value

        # Try to retrieve from 'content'
        content = self.__get_content__()
        if name in content:
            return content[name]

        # Otherwise, standard Python AttributeError
        raise AttributeError(f"'{this_cls.__name__}' object has no attribute '{name}'")
    
    def __setattr__(self, name: str, value: V) -> None:
        if object.__getattribute__(self, "__frozen__"):
            return
        if object.__getattribute__(self, "__auto_cast__"):
            expected = self.annotations.get(name)
            if expected:
                try:
                    value = expected(value)
                except Exception:
                    pass
        prev_value = object.__getattribute__(self, "content").get(name, None)
        if isinstance(prev_value, Field): 
            prev_value.value = value
        else:
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
        return self.__get_content__()[key]
    def __setitem__(self, key: str, value: V) -> None:
        if object.__getattribute__(self, "__frozen__"):
            return
        if object.__getattribute__(self, "__auto_cast__"):
            expected = self.annotations.get(key)
            if expected:
                try:
                    value = expected(value)
                except Exception:
                    pass
        prev_value = object.__getattribute__(self, "content").get(key, None)
        if isinstance(prev_value, Field): 
            prev_value.value = value
        else:
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

class FrozenData(Data):
    """Frozen Data is completely immutable and cannot be changed."""

    __slots__ = Data.__slots__ + ("__weakref__",)

    def __init__(self, value: Optional[DictSchema] = None, include_methods: bool = False, **kwargs: Any) -> None:
        super().__init__(value=value, frozen=True, include_methods=include_methods, **kwargs)
    
    def setdefault(self, key: str, default: Optional[V] = None) -> Optional[V]: return
    def pop(self, key: str, default: Optional[V] = None) -> Optional[V]: return
    def update(self, data: DictSchema) -> None: return
    def clear(self) -> None: return
    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError(f"Cannot modify frozen data: '{name}'")
    def __enter__(self) -> None: return
    def __exit__(self, *args: Any) -> None: return
    def __setitem__(self, key: str, value: Any) -> None:
        raise AttributeError(f"Cannot modify frozen data: '{key}'")
    def __delitem__(self, key: str) -> None: return