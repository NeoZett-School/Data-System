"""
Data package for handling data (information) and dataclasses.

This package does NOT replace the built-in dataclasses module, but rather 
provides a different approach to data handling using the Data class as a base.

Using the Data class allows for flexible and dynamic data structures, more so 
like dictionaries, but with added benefits such as type checking and custom methods.

It also provides a dataclass decorator to create Data-based dataclasses easily. 

This package is ideal for scenarios where data structures need to be dynamic yet 
type-safe, such as in configurations, data models, or any application. This will 
then provide a more flexible alternative to traditional dataclasses, giving you 
better access to information and storage, rather than strict field definitions.

The package has not been tested in multiple environments yet, so please report any issues. 
Expect a wide range of compatibility, since this package only relies on standard Python features, 
and complex legacy structures are mostly used to provide better performance and usability.
Copyright (c) 2024-2025 Neo Zetterberg
"""

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
import sys

class Module:
    """Module class for Data package."""

    # Dynamic attribute access and provision
    def __getattr__(self, name: str):
        match name:
            case "Data":
                return Data
            case "FrozenData":
                return FrozenData
            case "data_factory":
                return data_factory
            case "is_data_factory":
                return is_data_factory
            case "make_data_factory":
                return make_data_factory
            case "validate_data":
                return validate_data
            case "inspect_data":
                return inspect_data
            case "patch_data":
                return patch_data
            case "diff_data":
                return diff_data
            case "deep_update":
                return deep_update
            case "merge_data":
                return merge_data
            case "to_json_schema":
                return to_json_schema
            case "Module":
                return Module
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

sys.modules[__name__] = Module()