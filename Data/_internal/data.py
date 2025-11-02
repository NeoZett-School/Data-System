"""A flexible data container class that behaves like both a dictionary and an object with attributes."""

from typing import (
    Iterable, Set, Tuple, List, Dict, Any, Optional, Type, TypeVar, Generic, 
    Literal, overload, KeysView, ValuesView, ItemsView, Union, Callable, Self,
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

    _meta_cache: Dict[str, Any]

    __frozen__: bool
    __include_methods__: bool
    __auto_cast__: bool
    __strict_typing__: bool
    __meta_config__: Dict[str, Any]
    __fields__: Dict[str, Field]
    __slots__ = ("content", "annotations", "__frozen__", "__auto_cast__", "__strict_typing__", "__meta_config__", "__fields__", "__original__", "__was_frozen__",) # __weakref__ is already defined in generic

    def __init__(self, value: Optional[DictSchema] = None, frozen: bool = False, include_methods: bool = False, auto_cast: bool = True, strict_typing: bool = True, **kwargs: Any) -> None:
        """Initializes the Data object with optional dictionary content and keyword arguments."""

        prepared_content = {}

        for k, v in (value or {}).items():
            # Non-field values pass through
            if not isinstance(v, Field):
                prepared_content[k] = v
                continue

            # Skip class fields (static, not instance-linked)
            if getattr(v, "classfield", False):
                prepared_content[k] = v
                continue

            # Create independent copy
            field_copy = v.copy()
            field_copy.name = k
            field_copy.data = self  # <- link copied field, not original
            prepared_content[k] = field_copy
        
        for k, v in kwargs.items():
            prepared = prepared_content.get(k, None)
            if isinstance(prepared, Field) and not isinstance(prepared, ComputedField):
                prepared.value = v
                continue
            prepared_content[k] = v

        # Core attributes
        object.__setattr__(self, "annotations", {})
        object.__setattr__(self, "content", prepared_content)
        object.__setattr__(self, "_meta_cache", {}) # Create a _meta_cache for this object

        try:
            meta_cls = dict(type(self).__meta_config__)
        except AttributeError:
            meta_cls = {}
        object.__setattr__(self, "__meta_config__", meta_cls)

        # Config flags
        object.__setattr__(self, "__frozen__", frozen or self.meta.get("frozen", False))
        object.__setattr__(self, "__auto_cast__", auto_cast or self.meta.get("auto_cast", False))
        object.__setattr__(self, "__strict_typing__", strict_typing or self.meta.get("strict_typing", False))

        # Field registry (now fields are already linked)
        object.__setattr__(self, "__fields__", {k: v for k, v in prepared_content.items() if isinstance(v, Field)})
    
    @property
    def meta(self) -> Dict[str, Any]:
        """Allocate and retrieve relevant metadata for the Data object."""
        cls_meta = self.__class__.__meta_config__ or {}
        instance_meta = self.content.get("__meta_config__", {})
        merged = {}
        merged.update(cls_meta)
        merged.update(instance_meta)
        object.__setattr__(self, "_meta_cache", merged)
        return object.__getattribute__(self, "_meta_cache")
    
    @property
    def data(self) -> Dict[str, Any]:
        """Return resolved data values (with Field.value replaced)."""
        return self.get_content()
    
    @property
    def fields(self) -> Dict[str, Field]:
        self.__link_fields__()
        return object.__getattribute__(self, "__fields__")
    
    def __link_fields__(self):
        """Ensure all Field objects are linked to this Data instance."""
        object.__setattr__(self, "__fields__", {})
        for name, field in object.__getattribute__(self, "content").items():
            if isinstance(field, Field):
                object.__getattribute__(self, "__fields__")[name] = field
                field.name = name
                field.data = self
    
    def __check_type(self, value: Any, annotation: Type) -> bool:
        """Recursively checks if a value conforms to a given typing annotation."""
        origin = get_origin(annotation)
        args = get_args(annotation)

        # 1. Handle Field objects (Initial value resolution)
        if isinstance(value, Field):
            # Your existing logic to resolve Field to its value or default
            field = value
            value = field.value
            if value is None:
                if field.required:
                    return False
                value = field.default
                # If default is still None, proceed to check annotation for Optional/None

        # --- Core Type Logic ---

        # 2. Handle Simple/Non-Generic Types (origin is None)
        if origin is None:
            if annotation is Any or isinstance(annotation, TypeVar): 
                return True
            if annotation is type(None): # Handles explicit 'type(None)' annotation
                return value is None
            
            # Handle custom Data subclasses here for instance checks
            if isinstance(value, Data): 
                return isinstance(value, annotation) 

            # Handle built-in and simple classes (int, str, custom classes)
            try:
                return isinstance(value, annotation)
            except TypeError:
                # Catch cases where annotation is not a valid class (e.g., Literal, type(None) from get_args)
                return True 

        # --- Generic Type Logic ---

        # 3. Handle Union (including Optional)
        if origin is Union:
            # Optimization: Optional[T] is Union[T, NoneType]
            if type(None) in args and value is None:
                return True
            
            # Check if value matches any type in the Union
            return any(self.__check_type(value, arg) for arg in args)

        # 4. Handle Literal
        if origin is Literal:
            # Check if the value is one of the literal arguments
            return value in args

        # 5. Handle Callable
        if origin is Callable:
            if not callable(value):
                return False
            # Note: Checking signature is complex, usually just check if callable
            return True
        
        # 6. Handle Type/type (Type[T] or type[T])
        if origin is Type or origin is type:
            if not isinstance(value, type):
                return False
            if args:
                # Check if the class/type is a subclass of the annotated generic argument
                # e.g., value is a class, args[0] is the base class T
                target_class = args[0]
                if get_origin(target_class) is Union:
                    return any(issubclass(value, t) for t in get_args(target_class))
                return issubclass(value, target_class)
            return True # Type is generic (Type[Any])

        # 7. Handle Container Types (List, Dict, Tuple, Set, etc.)
        if origin in (list, List, set, Set, frozenset, FrozenSet):
            if not isinstance(value, origin):
                return False
            
            if args: # Annotated type (e.g., List[int])
                item_type = args[0]
                return all(self.__check_type(item, item_type) for item in value)
            return True # Non-annotated type (e.g., List)
            
        if origin in (tuple, Tuple):
            if not isinstance(value, origin):
                return False
                
            if args: # Annotated tuple (e.g., Tuple[int, str] or Tuple[int, ...])
                if len(args) == 2 and get_origin(args[1]) is Ellipsis: # Variable length Tuple[T, ...]
                    item_type = args[0]
                    return all(self.__check_type(item, item_type) for item in value)
                
                # Fixed-length tuple (e.g., Tuple[int, str])
                if len(value) != len(args):
                    return False 
                return all(self.__check_type(value[i], args[i]) for i in range(len(value)))
            return True # Non-annotated tuple (e.g., tuple)

        if origin in (dict, Dict):
            if not isinstance(value, origin):
                return False
                
            if len(args) == 2: # Annotated dictionary (e.g., Dict[str, int])
                key_type, value_type = args
                return all(self.__check_type(k, key_type) and self.__check_type(v, value_type)
                        for k, v in value.items())
            return True # Non-annotated dictionary (e.g., Dict)

        # --- Fallback for Subclasses ---

        # 8. Fallback for Generic Subclasses (like Data[Gene])
        try:
            # Check if value is an instance of the non-generic origin type
            if not isinstance(value, origin):
                return False
            
            # Further checks for generics like Data[V] (optional, complex)
            # If the origin has type arguments (args), you'd need custom logic 
            # to ensure the instance's type arguments match the annotation's.
            return True

        except TypeError: 
            # General catch-all for remaining types that are not usable with isinstance
            return True

        return False

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
        incorrect = []
        if object.__getattribute__(self, "__strict_typing__"):
            incorrect = self.__get_incorrect_typing__(annotations)
        for name, field in object.__getattribute__(self, "__fields__").items():
            if not isinstance(field, ComputedField) and (not field.validator(field.value or field.default) or (field.required and not field.value)):
                if not name in incorrect: incorrect.append(name)
        if incorrect:
            raise TypeError(f"Incorrect typing for fields: {', '.join(incorrect)}")
    
    def _resolve_value(self, value: Any) -> V:
        if isinstance(value, Field):
            return (value.value or value.default) if not isinstance(value, ComputedField) else value.value
        if isinstance(value, Data):
            return value.get_content()
        return value
    
    def get_content(self) -> DictSchema:
        return {k: self._resolve_value(v) for k, v in object.__getattribute__(self, "content").items()}
    
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
        content = dict(self.get_content())
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
        return object.__getattribute__(self, "content").keys()
    def values(self) -> ValuesView[V]:
        """Return a set-like object providing a view on the data's values."""
        return self.get_content().values()
    def items(self) -> ItemsView[str, V]:
        """Return a set-like object providing a view on the data's items."""
        return self.get_content().items()
    
    @overload
    def get(self, key: str, default: Literal[None] = None) -> Optional[V]: ...
    @overload
    def get(self, key: str, default: V) -> V: ...
    def get(self, key: str, default: Optional[V] = None) -> Optional[V]:
        """Return the value for key if key is in the dictionary, else default."""
        return self._resolve_value(object.__getattribute__(self, "content").get(key, default))
    
    @overload
    def setdefault(self, key: str, default: Literal[None] = None) -> Optional[V]: ...
    @overload
    def setdefault(self, key: str, default: V) -> V: ...
    def setdefault(self, key: str, default: Optional[V] = None) -> Optional[V]:
        content = object.__getattribute__(self, "content")
        if object.__getattribute__(self, "__frozen__"):
            return content.get(key, default)
        if not key in content:
            if isinstance(default, Field):
                object.__getattribute__(self, "__fields__")[key] = default
            result = self._resolve_value(default)
            self.__setitem__(key, default)
        result = self.__getitem__(key)
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
        content = object.__getattribute__(self, "content")
        if object.__getattribute__(self, "__frozen__"):
            return content.get(key, default)
        if isinstance(content.get(key, None), Field):
            object.__getattribute__(self, "__fields__").pop(key, None)
        return content.pop(key, self._resolve_value(default))
    
    def update(self, data: Union["Data", DictSchema]) -> None:
        if object.__getattribute__(self, "__frozen__"):
            return
        for k, v in data.items():
            self.__setitem__(k, v)
        self.__raise_typing_error__()
    
    def clear(self) -> None:
        if object.__getattribute__(self, "__frozen__"):
            return
        object.__getattribute__(self, "__fields__").clear()
        object.__getattribute__(self, "content").clear()
    
    def __call__(self, key: str, /, *args: Any, **kwargs: Any) -> Any:
        """Calls a callable stored in the data with the given key, passing any additional arguments."""
        value = object.__getattribute__(self, "content").get(key)
        if isinstance(value, ComputedField):
            value = lambda: value.value
        if not callable(value): 
            raise TypeError(f"'{key}' is not callable. Are you sure you are calling this correctly?")
        return value(*args, **kwargs)
    
    def __getattr__(self, name: str) -> V:
        content = object.__getattribute__(self, "content")
        if name in content:
            return self._resolve_value(content[name])
        raise AttributeError(f"{type(self).__name__} has no attribute '{name}'")
    
    def __setattr__(self, name: str, value: V) -> None:
        self.__setitem__(name, value)
    
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
        return self._resolve_value(object.__getattribute__(self, "content")[key])
    def __setitem__(self, key: str, value: V) -> None:
        content = object.__getattribute__(self, "content")
        if object.__getattribute__(self, "__frozen__"):
            return
        if object.__getattribute__(self, "__auto_cast__"):
            expected = self.annotations.get(key)
            if expected:
                try:
                    value = expected(value)
                except Exception:
                    pass
        if isinstance(value, Field):
            object.__getattribute__(self, "__fields__")[key] = value
            content[key] = value
        elif isinstance(content[key], Field) and not isinstance(content[key], ComputedField):
            content[key].value = value
        else: content[key] = value
        self.__raise_typing_error__()
    def __delitem__(self, key: str) -> None:
        if object.__getattribute__(self, "__frozen__"):
            return
        if key in object.__getattribute__(self, "__fields__"):
            del object.__getattribute__(self, "__fields__")[key]
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