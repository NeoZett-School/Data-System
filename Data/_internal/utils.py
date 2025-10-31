from typing import List, Dict, Union, Type, TypeVar, Literal, Generic, Optional, Any, overload
from .factory import data_factory, _Dataclass
from .fields import Field, ComputedField
from .data import Data, V

__all__ = (
    "is_data_factory", 
    "make_data_factory", 
    "validate_data", 
    "inspect_data", 
    "patch_data", 
    "diff_data", 
    "sync_data",  
    "to_schema", 
    "diff_schema", 
    "clone", 
    "pretty_repr", 
)

T = TypeVar("T", bound=Data)

class _TypedDataclass(Data[V]):
    ...

def is_data_factory(obj: Union[T, Type[T]], /) -> bool:
    """
    Checks if a class is a dataclass created using the `dataclass` function.

    Args:
        cls (T): The class to check.

    Returns:
        bool: True if the class is a dataclass, False otherwise.
    """
    cls = obj if isinstance(obj, type) else obj.__class__
    return issubclass(cls, _Dataclass)

@overload
def make_data_factory(
    cls: Type[T], /,
    value: Optional[Dict[str, V]] = None,
    decorate: Literal[False] = False,
    **kwargs: Any
) -> T: ...
@overload
def make_data_factory(
    cls: Type[T], /,
    value: Optional[Dict[str, V]] = None,
    decorate: Literal[True] = True,
    frozen: bool = False,
    include_methods: bool = False,
    **kwargs: Any
) -> _TypedDataclass[T]: ...

def make_data_factory(
    cls: Type[T], /,
    value: Optional[Dict[str, V]] = None,
    decorate: bool = False,
    frozen: bool = False,
    include_methods: bool = False,
    **kwargs: Any
) -> Union[T, _Dataclass[T]]:
    """
    Creates an instance of a dataclass, optionally decorating it first.
    """

    if decorate:
        cls = data_factory(cls, frozen=frozen, include_methods=include_methods)
    elif frozen or include_methods:
        raise ValueError("frozen/include_methods are only valid when decorate=True.")

    if not is_data_factory(cls):
        raise TypeError("The provided class is not a dataclass.")

    return cls(value=value, **kwargs)

def validate_data(data: "Data", strict: bool = False) -> List[str]:
    """
    Gather invalid fields from annotations and raise them if stricit is active.
    Otherwise, this will just returns invalid fields.
    """
    bad_fields = data.__get_incorrect_typing__()
    if strict and bad_fields:
        raise TypeError(f"Invalid fields: {', '.join(bad_fields)}")
    return bad_fields

def inspect_data(obj: Union[Type[Data], Data]) -> Dict[str, Any]:
    """
    Retrieve a detailed dictionary containing name and type annotiations.
    This will also conclude defaults and values, to that of the real value of the field.
    """
    cls = obj if isinstance(obj, type) else type(obj)
    data = obj if isinstance(obj, Data) else None
    defaults = {}
    for k in getattr(cls, "__annotations__", {}):
        if not hasattr(cls, k):
            continue
        value = getattr(cls, k, None)
        defaults[k] = value if not isinstance(value, Field) else value.default if not isinstance(value, ComputedField) else "<ComputedField>"
    return {
        "name": cls.__name__,
        "annotations": getattr(cls, "__annotations__", {}),
        "defaults": defaults,
        "values": data.to_dict() if data else None,
    }

def patch_data(data: Data, *, validate: bool = True, **updates: V) -> None:
    """Will update data. Sets annotiations according to the fields."""
    anns = getattr(data, "__annotations__", {})
    anns.update({k: type(v) for k, v in updates.items()})
    for k, v in updates.items():
        setattr(data, k, v)
    if validate:
        data.__raise_typing_error__()

def diff_data(a: Data, b: Data) -> Dict:
    "Retrieves fields that doesn't appear in the other's structure."
    diffs = {}
    for k, v in a.items():
        if b.get(k) != v:
            diffs[k] = (v, b.get(k))
    return diffs

def sync_data(target: Data, source: Data, *, overwrite: bool = False) -> None:
    """Copy missing or differing values from source to target."""
    for k, v in source.items():
        if overwrite or k not in target or target[k] != v:
            setattr(target, k, v)

def to_schema(cls: Type[Data]) -> Dict[str, Any]:
    schema = {"type": "object", "properties": {}}
    for k, v in getattr(cls, "__annotations__", {}).items():
        schema["properties"][k] = {"type": v}
    return schema

def diff_schema(a: Type[Data], b: Type[Data]) -> Dict[str, Dict[str, Any]]:
    """Compare field annotations between two Data types."""
    diffs = {}
    for k, v in a.__annotations__.items():
        if k not in b.__annotations__:
            diffs[k] = {"only_in": a.__name__}
        elif b.__annotations__[k] != v:
            diffs[k] = {"a": v, "b": b.__annotations__[k]}
    for k in b.__annotations__:
        if k not in a.__annotations__:
            diffs[k] = {"only_in": b.__name__}
    return diffs

def clone(data: Data, **updates: V) -> Data:
    """Clone a Data object with optional field overrides."""
    new = data.copy()
    for k, v in updates.items():
        setattr(new, k, v)
    return new

def pretty_repr(data: Data) -> str:
    """Return a formatted string showing fields, types, and values."""
    lines = []
    annotations = object.__getattribute__(data, "annotations")
    lines.append(f"<Data{f" \"{data.__class__.__name__}\"" if not data.__class__.__name__ == "Data" else ""} object>:")
    for k, v in data.items():
        t = annotations.get(k, type(v))
        lines.append(f"  {k}: {t.__name__} = {v!r}")
    return "\n".join(lines)
