from typing import Callable, Optional, Any
from data import V

__all__ = ("Field", "field", )

ValidatorLike = Callable[[V], Any]

class Field:
    def __init__(
        self, 
        default: Any = None, 
        validator: Optional[ValidatorLike] = None, 
        required: bool = False
    ) -> None: 
        ...

def field(
    *, 
    default: Any = None, 
    validator: Optional[ValidatorLike] = None, 
    required: bool = False
) -> Field: 
    ...