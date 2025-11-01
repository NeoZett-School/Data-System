from typing import TYPE_CHECKING, Callable, Type, Any
if TYPE_CHECKING:
    from factory import T
    from data import V

if TYPE_CHECKING:
    ValidatorLike = Callable[[V], Any]

class Field:
    default: Any
    default_factory: Type
    required: bool
    classfield: bool
    if TYPE_CHECKING:
        validator: ValidatorLike
        _value: V

    def __init__(
        self, *, 
        default: Any = None, 
        default_factory: Callable[[], Any] = None, 
        validator = None, 
        required: bool = False, 
        classfield: bool = False
    ) -> None:
        self.default = default
        self.default_factory = default_factory
        self.validator = validator or (lambda x: True)
        self.required = required
        self.classfield = classfield
        self._value = None
    
    def copy(self) -> "Field":
        return Field(default=self.default or self.default_factory(), default_factory=self.default_factory, validator=self.validator, required=self.required)
    
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
        classfield: bool

    def __init__(self, method, classfield: bool = False) -> None:
        self.method = method
        self.classfield = classfield
        self.data = None
        self.recursion = False
    
    def copy(self) -> "ComputedField":
        new_field = ComputedField(self.method, self.classfield)
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
    required: bool = False, 
    classfield: bool = False
) -> Field: 
    return Field(default=default, default_factory=default_factory, validator=validator, required=required, classfield=classfield)

def computed_field(method, classfield: bool = False) -> ComputedField:
    return ComputedField(method, classfield)