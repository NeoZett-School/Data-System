from typing import Type, Callable, Any
from ._internal import (
    Data, 
    FrozenData, 
    data_factory, 
    is_data_factory, 
    make_data_factory, 
    field, 
    validate_data, 
    inspect_data, 
    patch_data, 
    diff_data, 
    sync_data, 
    to_json_schema, 
    diff_schema, 
    clone, 
    pretty_repr, 
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
    field: CallableUtility
    validate_data: CallableUtility
    inspect_data: CallableUtility
    patch_data: CallableUtility
    diff_data: CallableUtility
    sync_data: CallableUtility
    to_json_schema: CallableUtility
    diff_schema: CallableUtility
    clone: CallableUtility
    pretty_repr: CallableUtility

__all__ = (
    'Data', 
    'FrozenData', 
    'data_factory', 
    'is_data_factory', 
    'make_data_factory', 
    'field', 
    'validate_data', 
    'inspect_data', 
    'patch_data', 
    'diff_data', 
    'sync_data', 
    'to_json_schema', 
    'diff_schema', 
    'clone', 
    'pretty_repr', 
    'Module',
)