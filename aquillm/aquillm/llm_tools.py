from dataclasses import dataclass 
from types import GenericAlias
from typing import get_type_hints, List
import inspect 
# {name : (description, type)}
parameters_type = dict[str, tuple[str, type]]

@dataclass 

class LLMTool:
    function: callable
    llm_definition: dict

    @classmethod
    def translate_type(cls, t: type | GenericAlias):
        allowed_primitives = {str: "string",
                              int: "integer",
                              bool: "boolean"}
        if isinstance(t, GenericAlias):
            if t.__origin__ != list or len(t.__args__) != 1 or t.__args__[0] not in allowed_primitives.keys():
                raise TypeError("Only lists of primitive types are supported for tool call containers")
            return {"type": "array", "items": cls.translate_type(t.__args__[0])}
        return {"type": allowed_primitives[t]}

    def __init__(self, tool: callable):
        if not hasattr(tool, "name") or not isinstance(tool.name, str):
            raise TypeError("Tool must have str `name` describing function use")
        if not hasattr(tool, "description") or not isinstance(tool.description, str):
            raise TypeError(f"Tool {tool.name} must have str `description` describing function use")
        if not hasattr(tool, "param_descs") or not isinstance(tool.param_descs, dict):
            raise TypeError(f"Tool {tool.name} must have dict `param_descs` describing all parameters")
        if not hasattr(tool, "required") or not isinstance(tool.required, list):
            raise TypeError(f"Tool {tool.name} must have list of required parameters")
        self.function = tool
        self.param_types = get_type_hints(tool.__call__)
        if set(self.param_types.keys()) != set(inspect.signature(tool.__call__).parameters.keys()):
            raise TypeError(f"Missing type annotations for tool {tool.name}")
        if set(tool.param_descs.keys()) != set(inspect.signature(tool.__call__).parameters.keys()):
            raise TypeError(f"Missing parameter descriptions for tool {tool.name}")
        self.llm_definition = {"name" : tool.name,
                          "description": tool.description,
                          "input_schema": {
                              "type" : "object",
                              "properties": {
                                  k: type(self).translate_type(v) | {"description": tool.param_descs[k]} for k, v in self.param_types.items()
                              }
                          },
                          "required": tool.required} 
        
    def __call__(self, *args, **kwargs) -> dict:
        try:
            ret = self.function(*args, **kwargs)
        except Exception as e:
            ret = {"exception": str(e)}
        return ret
    
class ExampleFunction:
    name = "Example"
    description = "Nonsense function that does nothing"
    param_descs = {"a": "a string", "b": "a number"}
    required = ['a', 'b']
    
    @staticmethod
    def __call__(a: str, b: list[int]):
        ret = ""
        for i in range(b[0]):
            ret += a
        return {"result" : ret}

