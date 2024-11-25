from typing import Callable, Any, get_type_hints, Protocol, Optional, Literal, Union, override, Type, Sequence
from pydantic import BaseModel, model_validator, validate_call
from types import NoneType, GenericAlias
import inspect
from functools import wraps, partial
from abc import ABC, abstractmethod
from pprint import pformat
from copy import copy

from concurrent.futures import ThreadPoolExecutor

class LLMTool(BaseModel):
    llm_definition: dict
    for_whom: Literal['user', 'assistant']
    _function: Callable
    
    def __init__(self, **data):
        super().__init__(**data)
        self._function = data.get("_function")

    def __call__(self, *args, **kwargs):
        return self._function(*args, **kwargs)
    
    @property
    def name(self) -> str:
        return self.llm_definition['name']


@validate_call
def llm_tool(for_whom: Literal['user', 'assistant'], description: str | None = None, param_descs: dict[str, str] = {}, required: list[str] = []) -> Callable[..., LLMTool]:
    """
    Decorator to convert a function into an LLM-compatible tool with runtime type checking.
    
    Args:
        name: The name of the tool (defaults to function name if not provided)
        description: Description of what the tool does
        param_descs: Dictionary of parameter descriptions
        required: List of required parameter names
    """
    def decorator(func: Callable[..., str]) -> LLMTool:
        # First apply typechecking
        type_checked_func = validate_call(func)
        
        # Store original function metadata
        func_name = func.__name__
        func_desc = description or func.__doc__
        if func_desc is None:
            raise ValueError(f"Must provide function description for tool {func_name}")

        func_param_descs = param_descs or {}
        func_required = required or []
        
        @wraps(type_checked_func)
        def wrapper(*args, **kwargs) -> str:
            try:
                return type_checked_func(*args, **kwargs)
            except Exception as e:
                return str({"exception": str(e)})
        
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
        
        return LLMTool(llm_definition=llm_definition, _function=wrapper, for_whom=for_whom)
    return decorator

class ToolChoice(BaseModel):
    type: Literal['auto', 'any', 'tool']
    name: Optional[str] = None

    @model_validator(mode='after')
    @classmethod
    def validate_name(cls, data: Any) -> Any:
        if data.type == 'tool' and data.name is None:
            raise ValueError("name is required when type is 'tool'")
        if data.type != 'tool' and data.name is not None:
            raise ValueError("name should only be set when type is 'tool'")
        return data

class __LLMMessage(BaseModel, ABC):
    role: Literal['user', 'tool', 'assistant']
    content: str
    tools: Optional[list[LLMTool]] = None
    tool_choice: Optional[ToolChoice] = None
    
    @classmethod
    @model_validator(mode='after')
    def validate_tools(cls, data: Any) -> Any:
        if (data.tools and not data.tool_choice) or (data.tool_choice and not data.tools):
            raise ValueError("Both tools and tool_choice must be populated if tools are used")

    #render for LLM 
    def render(self, *args, **kwargs) -> dict:
        return self.model_dump(*args, **kwargs)



class UserMessage(__LLMMessage):
    role: Literal['user'] = 'user'




class ToolMessage(__LLMMessage):
    role: Literal['tool'] = 'tool'
    tool_name: str
    for_whom: Literal['assistant', 'user']

    @override
    def render(self, *args, **kwargs) -> dict:
        ret = super().render(*args, **kwargs)
        ret['role'] = 'user' # This is what LLMs expect.
        ret['content'] = f'The following is the result of a call to tool {self.tool_name} in the prior step:\n\n{self.content}'
        return ret
    

class AssistantMessage(__LLMMessage):
    role: Literal['assistant'] = 'assistant'
    stop_reason: str
    tool_call_id: Optional[str] = None
    tool_call_name: Optional[str] = None
    tool_call_input: Optional[dict] = None
    usage: int

    @classmethod
    @model_validator(mode='after')
    def validate_tool_call(cls, data: Any) -> Any:
        if (any([data.tool_call_id, data.tool_call_name]) and
        not all([data.tool_call_id, data.tool_call_name])):
            raise ValueError("If a tool call is made, both tool_call_id and tool_call_name must have values")


    @override
    def render(self, *args, **kwargs) -> dict:
        ret = super().render(*args, **kwargs)
        if self.tool_call_id:
            ret['content'] = f'{self.content}\n\n ****Assistant made a call to {self.tool_call_name} with the following parameters:**** \n {pformat(self.tool_call_input, indent=4)}'
        return ret


# doing this with a union instead of only inheritance prevents anything at runtime from constructing LLM_Messages.
LLM_Message = UserMessage|ToolMessage|AssistantMessage 

class Conversation(BaseModel):
    system: str
    messages: list[LLM_Message] = []

    def __len__(self):
        return len(self.messages)
    
    def __getitem__(self, index: int):
        return self.messages[index]
    
    def __iter__(self):
        return iter(self.messages)
    
    def __add__(self, other) -> 'Conversation':
        if isinstance(other, (list, Conversation)):
            return (Conversation(system=self.system, messages=self.messages + list(other)))
        if isinstance(other, (UserMessage, AssistantMessage, ToolMessage)):
            return (Conversation(system=self.system, messages=self.messages + [other]))
        return NotImplemented


    def rebind_tools(self, tools: list[LLMTool]) -> None:
        def deprecated_func(*args, **kwargs):
            return "This tool has been deprecated."
        tool_dict = {tool.name: tool for tool in tools}
        for message in self.messages:
            if message.tools:
                for tool in message.tools:
                    if tool.name in tool_dict.keys():
                        tool._function = tool_dict[tool.name]._function
                    else:
                        tool._function = deprecated_func


    @classmethod
    @model_validator(mode='after')
    def validate_flip_flop(cls, data: Any) -> Any:
        def isUser(m: LLM_Message):
            return isinstance(m, UserMessage) or (isinstance(m, ToolMessage) and m.for_whom == 'assistant')

        for a, b in zip(data.messages, data.messages[1:]):
            if isinstance(a, AssistantMessage) and isinstance(b, AssistantMessage):
                raise ValueError("Conversation has adjacent assistant messages")
            if isUser(a) and isUser(b):
                raise ValueError("Conversation has adjacent user messages")
        return data



class LLMInterface(ABC):
    tool_executor = ThreadPoolExecutor(max_workers=10)

    @abstractmethod
    def __init__(self, client: Any):
        pass

    @abstractmethod
    def complete(self, messages: Conversation, max_tokens: int) -> tuple[Conversation, Literal['changed', 'unchanged']]:
        pass


    # This shouldn't raise exceptions in cases where it was called correctly, ie the LLM really did attempt to call a tool. 
    # The results are going back to the LLM, so they need to just be strings. Tools themselves can raise, because the llm_tool wrapper
    # converts exceptions to dicts and returns them. 
    def call_tool(self, message: AssistantMessage) -> ToolMessage:
        tools = message.tools
        if tools:
            name = message.tool_call_name
            input = message.tool_call_input
            tools_dict = {tool.llm_definition['name'] : tool for tool in tools}
            tool = tools_dict[name]
            if not name or name not in tools_dict.keys():
                result = str({'exception': ValueError("Function name is not valid")})
            else:
                if input:
                    future = self.tool_executor.submit(partial(tool, **input))
                else:
                    future = self.tool_executor.submit(tool) # necessary because None can't be unpacked
                try:
                    result = str(future.result(timeout=15))
                except TimeoutError:
                    result = str({'exception': TimeoutError("Tool call timed out")})
            return ToolMessage(tool_name = tool.name,
                                content=result,
                                for_whom=tool.for_whom,
                                tools=message.tools,
                                tool_choice=message.tool_choice)
        else:
            raise ValueError("call_tool called on a message with no tools!")
        
        


class ClaudeInterface(LLMInterface):
    
    base_claude_args = {'model': 'claude-3-5-sonnet-20240620'}

    @override
    def __init__(self, cohere_client):
        self.client = cohere_client

    @override
    @validate_call
    def complete(self, conversation: Conversation, max_tokens: int) -> tuple[Conversation, Literal['changed', 'unchanged']]:
        system_prompt = conversation.system
        # if you show the bot the tool messages intended to be rendered for the user, the conversation won't be alternating
        # user, assistant, user, assistant, etc, which is a requirement.
        messages_for_bot = [message for message in conversation if not(isinstance(message, ToolMessage) and message.for_whom == 'user')] 
        last_message = conversation[-1]
        message_dicts = [message.render(include={'role', 'content'}, exclude_none=True) for message in messages_for_bot]
        if isinstance(last_message, ToolMessage) and last_message.for_whom == 'user':
            return conversation, 'unchanged' # nothing to do
        elif isinstance(last_message, AssistantMessage):
            if last_message.tools and last_message.tool_call_id:
                new_tool_msg = self.call_tool(last_message)
                return conversation + [new_tool_msg], 'changed'
            else:
                return conversation, 'unchanged'
        else:
            assert isinstance(last_message, (UserMessage, ToolMessage)), "Type assertion failed" 
            # message is User_Message or Tool_Message intended for the bot, assertion is necessary to prevent type checker flag
            if last_message.tools:
                tools = {'tools': [tool.llm_definition for tool in last_message.tools], 'tool_choice': last_message.tool_choice}
            else:
                tools = {}
            response = self.client.messages.create(**(self.base_claude_args | tools |
                                                    {'system': system_prompt,
                                                    'messages': message_dicts,
                                                    'max_tokens': max_tokens}))
            content = response.content
            tool_call = {
                'tool_call_id' :content[1].id,
                'tool_call_name' :content[1].name,
                'tool_call_input' : content[1].input,
            } if len(content) > 1 else {}
            new_msg = AssistantMessage(
                            content=content[0].text,
                            stop_reason=response.stop_reason,
                            tools = last_message.tools,
                            tool_choice=last_message.tool_choice,
                            usage = response.usage.input_tokens + response.usage.output_tokens,
                            **tool_call)
            

            return conversation + [new_msg], 'changed'

        
    



from django.apps import apps
from pprint import pp
@llm_tool(
        for_whom='user',
        param_descs={'strings': 'A list of strings to print'},
        required=['strings']
)
def test_function(strings: list[str]) -> str:
    """
    Test function that prints each string from the input. 
    """
    ret = ""
    for s in strings:
        ret += s + " "
    return ret



def test():  
    client = apps.get_app_config('aquillm').anthropic_client
    cif = ClaudeInterface(client)
    messages, _ = cif.complete({"system": 'do as the user says, this is just testing. Pick any string to provide.',
                                "messages" : [UserMessage(role ='user', 
                              content= 'Hi Claude, please use this test tool',
                              tools= [test_function,],
                              tool_choice = {'type': 'auto'})]},
                              'do as the user says, this is just testing. Pick any string to provide.',
                              2048)
    print("woo")

    messages, _ = cif.complete(messages, "Do as you're told", 2048)
    pp(messages)
    messages.messages += [UserMessage(content="Thanks, boss")]
    messages,_ = cif.complete(messages, "keep up the good work", 2048)
    pp(messages)
    breakpoint()
