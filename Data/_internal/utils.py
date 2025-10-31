from typing import List, Dict, Union, Type, Any
from .factory import _Dataclass, T
from .data import Data

__all__ = (
    "is_data_factory", 
    "make_data_factory", 
    "validate_data", 
    "inspect_data", 
    "patch_data", 
    "deep_update", 
    "merge_data", 
    "to_json_schema",
)

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

def make_data_factory(cls: Type[T], /, **kwargs) -> T:
    """
    Creates an instance of a dataclass with the provided keyword arguments.

    Args:
        cls (T): The dataclass type.
        **kwargs: The fields and their values to initialize the dataclass.

    Returns:
        T: An instance of the dataclass.
    """
    if not is_data_factory(cls):
        raise TypeError("The provided class is not a dataclass.")
    return cls(**kwargs)

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
    return {
        "name": cls.__name__,
        "annotations": getattr(cls, "__annotations__", {}),
        "defaults": {
            k: getattr(cls, k, None)
            for k in getattr(cls, "__annotations__", {})
            if hasattr(cls, k)
        },
        "values": data.to_dict() if data else None,
    }

def patch_data(data: Data, *, validate: bool = True, **fields: Any) -> None:
    """Will update data. Sets annotiations according to the fields."""
    anns = getattr(data, "__annotations__", {})
    anns.update({k: type(v) for k, v in fields.items()})
    for k, v in fields.items():
        object.__setattr__(data, k, v)
    if validate:
        data.__raise_typing_error__()

def diff_data(a: "Data", b: "Data") -> Dict:
    "Retrieves fields that doesn't appear in the other's structure."
    diffs = {}
    for k, v in a.items():
        if b.get(k) != v:
            diffs[k] = (v, b.get(k))
    return diffs

def deep_update(a: "Data", b: "Data") -> None:
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(a.get(k), dict):
            deep_update(a[k], v)
        else:
            a[k] = v

def merge_data(a: "Data", b: "Data", *, deep: bool = False) -> "Data":
    """Return a new Data instance combining fields from both (b overrides a)."""
    new_dict = a.to_dict().copy()
    for k, v in b.items():
        if deep and isinstance(v, dict) and isinstance(new_dict.get(k), dict):
            new_dict[k].update(v)
        else:
            new_dict[k] = v
    return type(a)(new_dict)

def to_json_schema(cls: Type["Data"]) -> Dict[str, Any]:
    schema = {"type": "object", "properties": {}}
    for k, v in getattr(cls, "__annotations__", {}).items():
        t = getattr(v, "__name__", str(v))
        schema["properties"][k] = {"type": t.lower()}
    return schema