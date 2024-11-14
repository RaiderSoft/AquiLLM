from typing import Callable, Any, get_type_hints, Protocol, Optional, Literal, Union
from pydantic import BaseModel, model_validator, validate_call
from types import NoneType, GenericAlias
import inspect
from functools import wraps
from abc import ABC, abstractmethod


class LLMTool(BaseModel):
    llm_definition: dict
    for_whom = Literal['user', 'assistant']
    _function: Callable
    
    def __init__(self, **data):
        super().__init__(**data)
        self._function = data.get("_function")

    def __call__(self, *args, **kwargs):
        return self._function(*args, **kwargs)


@validate_call
def llm_tool(for_whom: Literal['user', 'assistant'], name: str | None = None, description: str | None = None, param_descs: dict[str, str] = {}, required: list[str] = []) -> Callable[..., LLMTool]:
    """
    Decorator to convert a function into an LLM-compatible tool with runtime type checking.
    
    Args:
        name: The name of the tool (defaults to function name if not provided)
        description: Description of what the tool does
        param_descs: Dictionary of parameter descriptions
        required: List of required parameter names
    """
    def decorator(func: Callable[..., Any]) -> LLMTool:
        # First apply typechecking
        type_checked_func = validate_call(func)
        
        # Store original function metadata
        func_name = name or func.__name__
        func_desc = description or func.__doc__
        if func_desc is None:
            raise ValueError(f"Must provide function description for tool {func_name}")

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
        llm_definition = {
            "name": func_name,
            "description": func_desc,
            "input_schema": {
                "type": "object",
                "properties": {
                    k: translate_type(v) | {"description": func_param_descs[k]} 
                    for k, v in param_types.items()
                },
                "required": func_required
            },
        }
        
        return LLMTool(llm_definition=llm_definition, _function=wrapper)
    return decorator

class ToolChoice(BaseModel):
    type: Literal['auto', 'any', 'tool']
    name: str | None = None

    @model_validator(mode='after')
    @classmethod
    def validate_name(cls, data: Any) -> Any:
        if data.type == 'tool' and data.name is None:
            raise ValueError("name is required when type is 'tool'")
        if data.type != 'tool' and data.name is not None:
            raise ValueError("name should only be set when type is 'tool'")
        return data

class LLM_Message(BaseModel, ABC):

    # for everything
    role: Literal['user', 'assistant', 'tool']
    content: str

    # for user messages
    tools: Optional[list[LLMTool]] = None
    tool_choice: Optional[ToolChoice] = None

    # for assistant messages
    stop_reason: Optional[str] = None
    tool_call_id: Optional[str] = None
    tool_call_name: Optional[str] = None
    tool_call_input: Optional[dict] = None



    @model_validator(mode='after')
    @classmethod
    def check_roles(cls, data: Any) -> Any:
        if data.role in ('user', 'tool') and any(map(lambda x: x is not None,
                                           [data.stop_reason, data.tool_call_id, data.tool_call_name, data.tool_call_input],
                                    )):
            raise ValueError("User and tool messages should not have fields reserved for assistant messages.")
        if data.role in ('assistant', 'tool') and any(map(lambda x: x is not None,
                                            [data.tools, data.tool_choice])):
            raise ValueError("Assistant and tool messages should not have fields reserved for user messages.")
        if data.tools is not None and data.tool_choice is None:
            raise ValueError("If tools are used, tool choice must be specified")
        return data



class LLM_Interface(ABC):
    @abstractmethod
    def __init__(self, client: Any):
        pass

    @abstractmethod
    def complete(self, messages: list[LLM_Message], system_prompt: str, max_tokens: int) -> LLM_Message:
        pass


class Claude_Interface(LLM_Interface):
    
    claude_args = {'model': 'claude-3-5-sonnet-20240620'}


    def __init__(self, cohere_client):
        self.client = cohere_client

    @validate_call
    def complete(self, messages: list[LLM_Message], system_prompt: str, max_tokens: int) -> LLM_Message:
        message_dicts = [message.model_dump(include={'role', 'content'}, exclude_none=True) for message in messages]
        if messages[-1].tools:
            tools = {'tools': [tool.llm_definition for tool in messages[-1].tools]}
        else:
            tools = {}
        tool_choice = messages[-1].tool_choice
        response = self.client.messages.create(**(self.claude_args | tools |
                                               {'system': system_prompt,
                                                'messages': message_dicts,
                                                'max_tokens': max_tokens,
                                                'tool_choice': tool_choice}))
        content = response.content
        return LLM_Message(role='assistant',
                           content=content[0].text,
                           tool_call_id=content[1].id or None,
                           tool_call_name=content[1].name or None,
                           tool_call_input = content[1].input or None)
        
    
        


from django.apps import apps
from pprint import pp
@llm_tool(
        for_whom='user',
        param_descs={'strings': 'A list of strings to print'},
        required=['strings']
)
def test_function(strings: list[str]):
    """
    Test function that prints each string from the input. 
    """
    for s in strings:
        print(s)

def test():  
    client = apps.get_app_config('aquillm').anthropic_client
    cif = Claude_Interface(client)
    response = cif.complete([{'role': 'user',
                              'content': 'Hi Claude, please use this test tool',
                              'tools': [test_function,],
                              'tool_choice': {'type': 'auto'}}],
                              'do as the user says, this is just testing. Pick any string to provide.',
                              2048)
    print("woo")
    pp(response)
    breakpoint()
