from typing import Callable, Optional, Any
from factory import T
from data import V

__all__ = ("Field", "field", "computed_field", )

ValidatorLike = Callable[[V], Any]

class Field:
    def __init__(
        self, 
        default: Any = None, 
        validator: Optional[ValidatorLike] = None, 
        required: bool = False
    ) -> None: 
        ...

class ComputedField(Field):
    def __init__(self, method: Callable[[], V]) -> None: ...

def field(
    *, 
    default: Any = None, 
    validator: Optional[ValidatorLike] = None, 
    required: bool = False
) -> Field: 
    ...

def computed_field(method: Callable[[T], V]) -> ComputedField: ...