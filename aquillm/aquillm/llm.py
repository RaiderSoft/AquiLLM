from typing import Callable, Any, get_type_hints, GenericAlias
import inspect
from functools import wraps
from typeguard import typechecked



@typechecked
def llm_tool(name: str = None, description: str = None, param_descs: dict[str, str] = None, required: list[str] = None):
    """
    Decorator to convert a function into an LLM-compatible tool with runtime type checking.
    
    Args:
        name: The name of the tool (defaults to function name if not provided)
        description: Description of what the tool does
        param_descs: Dictionary of parameter descriptions
        required: List of required parameter names
    """
    def decorator(func: callable) -> callable:
        # First apply typechecking
        type_checked_func = typechecked(func)
        
        # Store original function metadata
        func_name = name or func.__name__
        func_desc = description or func.__doc__ or ""
        func_param_descs = param_descs or {}
        func_required = required or []
        
        @wraps(type_checked_func)
        def wrapper(*args, **kwargs):
            try:
                return type_checked_func(*args, **kwargs)
            except Exception as e:
                return {"exception": str(e)}
        
        def translate_type(t: type | GenericAlias) -> dict:
            allowed_primitives = {
                str: "string",
                int: "integer",
                bool: "boolean"
            }
            if isinstance(t, GenericAlias):
                if t.__origin__ != list or len(t.__args__) != 1 or t.__args__[0] not in allowed_primitives.keys():
                    raise TypeError("Only lists of primitive types are supported for tool call containers")
                return {"type": "array", "items": translate_type(t.__args__[0])}
            return {"type": allowed_primitives[t]}
        

        # Get and validate type hints
        param_types = get_type_hints(func)
        param_types.pop("return", None)
        signature_names = set(inspect.signature(func).parameters.keys())
        
        if set(param_types.keys()) != signature_names:
            raise TypeError(f"Missing type annotations for tool {func_name}")
        if set(func_param_descs.keys()) != signature_names:
            raise TypeError(f"Missing parameter descriptions for tool {func_name}")
            
        # Create LLM definition
        wrapper.llm_definition = {
            "name": func_name,
            "description": func_desc,
            "input_schema": {
                "type": "object",
                "properties": {
                    k: translate_type(v) | {"description": func_param_descs[k]} 
                    for k, v in param_types.items()
                }
            },
            "required": func_required
        }
        
        return wrapper
    return decorator


