from json import loads, dumps

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async, aclose_old_connections

from django.contrib.auth.models import User
from django.apps import apps

from pydantic import ValidationError
from pydantic_core import to_jsonable_python
from aquillm import llm
from aquillm.llm import UserMessage, Conversation,LLMTool, test_function, ToolChoice, llm_tool, ToolResultDict
from aquillm.settings import DEBUG

from aquillm.models import TextChunk, Collection, CollectionPermission, WSConversation


from django.template import Engine, Context


# necessary so that when collections are set inside the consumer, it changes inside the vector_search closure as well. 
class CollectionsRef:
    def __init__(self, collections: list[int]):
        self.collections = collections

def get_vector_search_func(user: User, col_ref: CollectionsRef): 
    @llm_tool(
        param_descs={"search_string": "The string to search by. Often it helps to phrase it as a question. ",
                     "top_k": "The number of results to return. Start low and increase if the desired information is not found. Go no higher than about 15."},
        required=['search_string', 'top_k'],
        for_whom='assistant'

    )
    def vector_search(search_string: str, top_k: int) -> ToolResultDict:
        """
        Uses a combination of vector search, trigram search and reranking to search the documents available to the user.
        """
        docs = Collection.get_user_accessible_documents(user, Collection.objects.filter(id__in=col_ref.collections))
        if not docs:
            return {"exception": "No documents to search! Either no collections were selected, or the selected collections are empty."}
        _,_,results = TextChunk.text_chunk_search(search_string, top_k, docs)
        ret = {"result": {f"[Result {i+1}] -- {chunk.document.title} chunk #: {chunk.chunk_number} chunk_id:{chunk.id}": chunk.content for i, chunk in enumerate(results)}}
        return ret
    
    return vector_search


def get_more_context_func(user: User) -> LLMTool:
    @llm_tool(
            for_whom='assistant',
            required=['adjacent_chunks', 'chunk_id'],

            param_descs={'chunk_id': 'ID number of the chunk for which more context is desired',
                         'adjacent_chunks': 'How many chunks on either side to return. Start small and work up, if you think expanding the context will provide more useful info. Go no higher than 10.'},
    )
    def more_context(chunk_id: int, adjacent_chunks: int) -> ToolResultDict:
        """
        Get adjacent text chunks on either side of a given chunk.
        Use this when a search returned something relevant, but it seemed like the information was cut off.
        """
        if adjacent_chunks < 1 or adjacent_chunks > 10:
            return {"exception": f"Invalid value for adjacent_chunks!"}
        central_chunk = TextChunk.objects.filter(id=chunk_id).first()
        if central_chunk is None:
            return {"exception": f"Text chunk {chunk_id} does not exist!"}
        if not central_chunk.document.collection.user_can_view(user):
            return {"exception": f"User cannot access document containing {chunk_id}!"}
        central_chunk_number = central_chunk.chunk_number
        bottom = central_chunk_number - adjacent_chunks
        top = central_chunk_number + adjacent_chunks
        window = TextChunk.objects.filter(doc_id=central_chunk.doc_id, chunk_number__in=range(bottom, top+1)).order_by('chunk_number')
        text_blob = "".join([chunk.content for chunk in window])
        return {"result": f"chunk_numbers:{window.first().chunk_number} -> {window.last().chunk_number} \n\n {text_blob}"}
    return more_context


class ChatConsumer(AsyncWebsocketConsumer):
    llm_if: llm.LLMInterface = apps.get_app_config('aquillm').llm_interface
    db_convo: WSConversation = None
    convo: Conversation = None
    tools: list[LLMTool] = []
    user: User = None


    # used for if the chat is in a state where nothing further should happen.
    # disables the receive handler
    dead: bool = False 
    
    
    col_ref = CollectionsRef([])
    
    @database_sync_to_async
    def __save(self):
        self.db_convo.convo = to_jsonable_python(self.convo)
        if len(self.db_convo.convo['messages']) >= 2 and not self.db_convo.name:
            self.db_convo.set_name()
        self.db_convo.save()

    @database_sync_to_async
    def __get_convo(self, convo_id: int, user: User):
        convo = WSConversation.objects.filter(id=convo_id).first()
        if convo: 
            if convo.owner == user:
                return convo
            else:
                return None
        return convo
        
    @database_sync_to_async
    def __get_all_user_collections(self):
        self.col_ref.collections = [col_perm.collection.id for col_perm in CollectionPermission.objects.filter(user=self.user)]
    
    async def connect(self):

        async def send_func(convo: Conversation):
            self.convo = convo
            await self.send(text_data=dumps({"conversation": to_jsonable_python(self.convo) }))
            await self.__save()

        await self.accept()
        self.user = self.scope['user']
        await self.__get_all_user_collections()
        self.tools = [test_function,
                      get_vector_search_func(self.user, self.col_ref),
                      get_more_context_func(self.user)]
        convo_id = self.scope['url_route']['kwargs']['convo_id']
        self.db_convo = await self.__get_convo(convo_id, self.user)
        if self.db_convo is None:
            self.dead = True
            await self.send('{"exception": "Invalid chat_id"}')
            
            return
        try:
            self.convo = Conversation.model_validate(self.db_convo.convo)
            self.convo.rebind_tools(self.tools)
            await self.llm_if.spin(self.convo, max_func_calls=5, max_tokens=2048, send_func=send_func)
            return 
        except Exception as e:
            if DEBUG:
                raise e
            else:
                await self.send(text_data='{"exception": "A server error has occurred. Try reloading the page"}')
                return


    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):

        async def send_func(convo: Conversation):
            await aclose_old_connections()
            self.convo = convo
            await self.send(text_data=dumps({"conversation": to_jsonable_python(self.convo)}))
            await self.__save()

        async def append(data: dict):
            self.col_ref.collections = data['collections']
            self.convo += UserMessage.model_validate(data['message'])
            self.convo[-1].tools = self.tools
            self.convo[-1].tool_choice = ToolChoice(type='auto')
            await self.__save()

        async def rate(data: dict):
            message = [message for message in self.convo if str(message.message_uuid) == data['uuid']][0]
            message.rating = data['rating']
            await self.__save()

        if DEBUG:
            print(f"Recieved ws message:\n{text_data}")
        if not self.dead:
            try:
                data = loads(text_data)
                action = data.pop('action', None)
                if action == 'append':
                    await append(data)
                elif action == 'rate':
                    await rate(data)
                else:
                    raise ValueError(f'Invalid action "{action}"')
                await self.llm_if.spin(self.convo, max_func_calls=5, max_tokens=2048, send_func=send_func)
            except Exception as e:
                if DEBUG:
                    raise e
                else:
                    await self.send(text_data='{"exception": "A server error has occurred. Try reloading the page"}')

