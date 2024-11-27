from json import loads, dumps

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.auth import AuthMiddlewareStack

from django.contrib.auth.models import User
from django.apps import apps

from pydantic import ValidationError

from aquillm import llm
from aquillm.llm import UserMessage, Conversation,LLMTool, test_function, ToolChoice, llm_tool
from aquillm.settings import DEBUG

from aquillm.models import TextChunk, Collection


from django.template import Engine, Context



RAG_PROMPT_STRING = """
RAG Search Results:

{% for chunk in chunks %}
    [{{ forloop.counter }}] {{ chunk.document.title }} chunk #{{chunk.chunk_number}}

    {{ chunk.content }}

{% endfor %}
"""

search_result_template = Engine().from_string(RAG_PROMPT_STRING)

def get_vector_search_func(user: User):
    @llm_tool(
        param_descs={"search_string": "The string to search by. Often it helps to phrase it as a question. ",
                     "top_k": "The number of results to return. Start low and increase if the desired information is not found. Go no higher than about 15."},
        required=['search_string', 'top_k'],
        for_whom='assistant'

    )
    def vector_search(search_string: str, top_k: int) -> str:
        """
        Uses a combination of vector search, trigram search and reranking to search the documents available to the user.
        """
        docs = Collection.get_user_accessible_documents(user)
        _,_,results = TextChunk.text_chunk_search(search_string, top_k, docs)

        return search_result_template.render(Context({'chunks': results}))
    
    return vector_search



class ChatConsumer(AsyncWebsocketConsumer):
    llm_if: llm.LLMInterface = apps.get_app_config('aquillm').llm_interface
    convo: Conversation = Conversation(system="You are a helpful assistant.")
    tools: list[LLMTool] = [test_function]

    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        if DEBUG:
            print(f"Recieved ws message:\n{text_data}")
        async def send_func(convo: Conversation):
            self.convo = convo
            await self.send(text_data=dumps({"conversation": self.convo.model_dump()}))


        try:
            data = loads(text_data)
            action = data.pop('action', None)
            if action == 'append':
                self.convo += UserMessage.model_validate(data['message'])
                self.convo[-1].tools = self.tools + [get_vector_search_func(self.scope["user"])]
                self.convo[-1].tool_choice = ToolChoice(type="auto")
            elif action == 'replace':
                system = self.convo.system
                self.convo = Conversation.model_validate({'system': system, 'messages': data['messages']})
                self.convo[-1].tools = self.tools + [get_vector_search_func(self.scope["user"])]
                self.convo[-1].tool_choice = ToolChoice(type="auto")
            else:
                raise ValueError(f'Invalid action {action}')
            await self.llm_if.spin(self.convo, max_func_calls=5, max_tokens=2048, send_func=send_func)
        except Exception as e:
            if DEBUG:
                raise e
            else:
                await self.send(text_data='{"exception": "A server error has occurred. Try reloading the page"}')

