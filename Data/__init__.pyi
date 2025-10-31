from typing import Type, Callable, Any
from ._internal import (
    Data, 
    FrozenData, 
    data_factory, 
    is_data_factory, 
    make_data_factory,
    validate_data,
    inspect_data,
    patch_data, 
    diff_data, 
    deep_update, 
    merge_data, 
    to_json_schema
)

CallableUtility = Callable[(...), Any]
DataFactoryDecorator = Callable[(...), Any]

class Module: 
    # Basic Type defintions
    Data: Type[Data]
    FrozenData: Type[FrozenData]
    data_factory: DataFactoryDecorator
    is_data_factory: CallableUtility
    make_data_factory: CallableUtility
    validate_data: CallableUtility
    inspect_data: CallableUtility
    patch_data: CallableUtility
    diff_data: CallableUtility
    deep_update: CallableUtility
    merge_data: CallableUtility
    to_json_schema: CallableUtility

__all__ = (
    'Data', 
    'FrozenData', 
    'data_factory', 
    'is_data_factory', 
    'make_data_factory', 
    'validate_data', 
    'inspect_data', 
    'patch_data', 
    'diff_data', 
    'deep_update', 
    'merge_data', 
    'to_json_schema', 
    'Module',
)