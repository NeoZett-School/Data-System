from typing import TYPE_CHECKING, Callable, Any
if TYPE_CHECKING:
    from data import Data, V

if TYPE_CHECKING:
    ValidatorLike = Callable[[V], Any]

class Field:
    default: Any
    required: bool
    if TYPE_CHECKING:
        validator: ValidatorLike
        _value: V

    def __init__(
        self, 
        default: Any = None, 
        validator = None, 
        required: bool = False
    ) -> None:
        self.default = default
        self.validator = validator or (lambda x: True)
        self.required = required
        self._value = None
    
    @property
    def value(self) -> Any:
        return self._value
    
    @value.setter
    def value(self, new: Any) -> None:
        self._value = new

class ComputedField(Field):
    if TYPE_CHECKING:
        method: Callable[[Data], V]
        data: Data
        recursion: bool

    def __init__(self, method) -> None:
        self.method = method
        self.data = None
        self.recursion = False
    
    @property
    def value(self) -> Any:
        if not self.recursion:
            self.recursion = True
            result = self.method(self.data)
            self.recursion = False
            return result
    
    @value.setter
    def value(self, new: Any) -> None:
        pass

def field(
    *, 
    default: Any = None, 
    validator = None, 
    required: bool = False
) -> Field: 
    return Field(default, validator, required)

def computed_field(method) -> ComputedField:
    return ComputedField(method)