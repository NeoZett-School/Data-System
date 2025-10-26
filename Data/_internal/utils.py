from typing import Union, Type
from .factory import _Dataclass, T

__all__ = ("is_data_factory", "make_data_factory",)

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