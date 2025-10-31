from typing import TYPE_CHECKING, Callable, Any
if TYPE_CHECKING:
    from factory import T
    from data import V

if TYPE_CHECKING:
    ValidatorLike = Callable[[V], Any]

class Field:
    default: Any
    required: bool
    if TYPE_CHECKING:
        validator: ValidatorLike
        _value: V

    def __init__(
        self, *, 
        default: Any = None, 
        default_factory: Callable[[], Any] = None, 
        validator = None, 
        required: bool = False
    ) -> None:
        if default and default_factory: raise OverflowError("Cannot combine both default and default_factory. Chose one.")
        self.default = default if not default_factory else default_factory()
        self.validator = validator or (lambda x: True)
        self.required = required
        self._value = None
    
    def copy(self) -> "Field":
        return Field(default=self.default, validator=self.validator, required=self.required)
    
    @property
    def value(self) -> Any:
        return self._value
    
    @value.setter
    def value(self, new: Any) -> None:
        self._value = new

class ComputedField(Field):
    if TYPE_CHECKING:
        method: Callable[[T], V]
        data: T
        recursion: bool

    def __init__(self, method) -> None:
        self.method = method
        self.data = None
        self.recursion = False
    
    def copy(self) -> "ComputedField":
        new_field = ComputedField(self.method)
        new_field.data = self.data
        return new_field
    
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
    default_factory: Callable[[], Any] = None, 
    validator = None, 
    required: bool = False
) -> Field: 
    return Field(default=default, default_factory=default_factory, validator=validator, required=required)

def computed_field(method) -> ComputedField:
    return ComputedField(method)