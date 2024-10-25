from dataclasses import dataclass 
from types import GenericAlias
from typing import get_type_hints, List
import inspect 
from typeguard import typechecked
# {name : (description, type)}
parameters_type = dict[str, tuple[str, type]]


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
        param_types = get_type_hints(tool)
        param_types.pop("return", None)

        signature_names = set(inspect.signature(tool).parameters.keys())
        if set(param_types.keys()) != signature_names:
            raise TypeError(f"Missing type annotations for tool {tool.name}")
        if set(tool.param_descs.keys()) != signature_names:
            raise TypeError(f"Missing parameter descriptions for tool {tool.name}")
        self.llm_definition = {"name" : tool.name,
                          "description": tool.description,
                          "input_schema": {
                              "type" : "object",
                              "properties": {
                                  k: type(self).translate_type(v) | {"description": tool.param_descs[k]} for k, v in param_types.items()
                              }
                          },
                          "required": tool.required} 
        
    def __call__(self, *args, **kwargs) -> dict:
        try:
            ret = self.function(*args, **kwargs)
        except Exception as e:
            ret = {"exception": str(e)}
        return ret



# example of how to create a function compatible with LLMTool
# @typechecked
# def do_nothing(a: str, b: list[int]) -> dict:
#         ret = ""
#         for i in range(b[0]):
#             ret += a
#         return {"result" : ret}

# do_nothing.name = "example"
# do_nothing.description = "Nonsense function that does nothing"
# do_nothing.param_descs = {"a": "a string", "b": "a number"}
# do_nothing.required = ['a', 'b']


# if __name__ == "__main__": 
#     tool = LLMTool(do_nothing)
#     ret = tool("Test", [4])

#     print(ret)
#     print(tool.llm_definition)

