"""
Common type conversion utilities to avoid using eval().
This module provides safe type conversion from string type names to type objects.
"""
from typing import Type, Union

# Safe type mapping to replace eval()
TYPE_MAP = {
    "int": int,
    "str": str,
    "bool": bool,
    "float": float,
    "list": list,
    "dict": dict,
}


def safe_type_convert(type_name: Union[str, Type]) -> Type:
    """Safely convert type string to type object without using eval()
    
    Args:
        type_name: Either a string name of a type or a type object
        
    Returns:
        Type object corresponding to the type name
        
    Examples:
        >>> safe_type_convert("int")
        <class 'int'>
        >>> safe_type_convert(int)
        <class 'int'>
    """
    if isinstance(type_name, str):
        return TYPE_MAP.get(type_name, str)
    return type_name
