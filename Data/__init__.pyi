from typing import Type
from ._internal import (
    Data, data_factory, is_data_factory, make_data_factory
)
class Module: 
    # Basic Type defintions
    Data: Type[Data]
    dataclass: Type[data_factory]
    is_data_factory: Type[is_data_factory]
    make_data_factory: Type[make_data_factory]
__all__ = (
    'Data', 
    'data_factory', 
    'is_data_factory', 
    'make_data_factory', 
    'Module',
)