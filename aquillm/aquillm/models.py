from django.db import models, transaction
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from pgvector.django import VectorField, L2Distance, HnswIndex
from django.apps import apps
from django.core.exceptions import ValidationError, ObjectDoesNotExist

from tenacity import retry, wait_exponential
import uuid

from django.contrib.auth.models import User
from pypdf import PdfReader

import functools 

# for hashing full_text of documents to ensure unique contents
import hashlib

from django.template import Context
from django.core.serializers.json import DjangoJSONEncoder
import json
import logging
from django.db.models.query import QuerySet
from typing import  List, Type, Tuple


from django.core.exceptions import ValidationError
from django.contrib.postgres.search import TrigramSimilarity

import concurrent.futures

from django.db import DatabaseError
from django.db.models import Case, When

from .utils import get_embedding

logger = logging.getLogger(__name__)

class CollectionQuerySet(models.QuerySet):
    def filter_by_user_perm(self, user, perm='VIEW'):
        perm_options = []
        if perm == 'VIEW':
            perm_options = ['VIEW', 'EDIT', 'MANAGE']
        elif perm == 'EDIT':
            perm_options = ['EDIT', 'MANAGE']
        elif perm == 'MANAGE':
            perm_options = ['MANAGE']
        else:
            raise ValueError(f"Invalid Permission type {perm}")

        return self.filter(id__in=[col_perm.collection.pk for col_perm in CollectionPermission.objects.filter(user=user, permission__in=perm_options)])


class Collection(models.Model):
    name = models.CharField(max_length=100)
    users = models.ManyToManyField(User, through='CollectionPermission')
    objects = CollectionQuerySet.as_manager()
    def user_has_permission_in(self, user, permissions):
        return CollectionPermission.objects.filter(
            user=user,
            collection=self,
            permission__in=permissions
        ).exists()
    
    def user_can_view(self, user):
        return self.user_has_permission_in(user, ['VIEW', 'EDIT', 'MANAGE'])
    
    def user_can_edit(self, user):
        return self.user_has_permission_in(user, ['EDIT', 'MANAGE'])
    
    def user_can_manage(self, user):
        return self.user_has_permission_in(user, ['MANAGE'])
    
    # returns a list of documents, not a queryset.
    @classmethod
    def get_user_accessible_documents(cls, user, collections=None, perm='VIEW'):
        if collections is None:
            collections = cls.objects.all()

        collections = collections.filter_by_user_perm(user, perm)
        documents = functools.reduce(lambda l, r: l + r, [list(x.objects.filter(collection__in=collections)) for x in DESCENDED_FROM_DOCUMENT])
        return documents




    def __str__(self):
        return f'{self.name}'
    

class CollectionPermission(models.Model):
    PERMISSION_CHOICES = [
        ('VIEW', 'View'),
        ('EDIT', 'Edit'),
        ('MANAGE', 'Manage')
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    permission = models.CharField(max_length=10, choices=PERMISSION_CHOICES)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'collection'],
                name='unique_permission_constraint')
        ]

    def save(self, *args, **kwargs):
        with transaction.atomic():
            existing_permission = CollectionPermission.objects.filter(
                user=self.user,
                collection=self.collection
            ).first()

            if existing_permission and existing_permission.id != self.id:
                existing_permission.delete()

            super().save(*args, **kwargs)
            
# returns a list of objects, not a queryset!
def get_user_accessible_documents(user, collections=None, perm='VIEW'):

    if collections is None:
        collections = Collection.objects.all()

    collections = collections.filter_by_user_perm(user, perm)
    documents = functools.reduce(lambda l, r: l + r, [list(x.objects.filter(collection__in=collections)) for x in DESCENDED_FROM_DOCUMENT])
    return documents


class Document(models.Model):
    pkid = models.BigAutoField(primary_key=True, editable=False)
    id = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)

    title = models.CharField(max_length=200)
    full_text = models.TextField()
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    full_text_hash = models.CharField(max_length=64, db_index=True)
    ingested_by = models.ForeignKey(User, on_delete=models.RESTRICT)
    ingestion_date = models.DateTimeField(auto_now_add=True)
    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=['collection', 'full_text_hash'],
                name='%(class)s_document_collection_unique'
            )
        ]

    def save(self, *args, **kwargs):
        if len(self.full_text) < 100:
            raise ValidationError("The full text of a document must be at least 100 characters long.")
        self.full_text_hash = hashlib.sha256(self.full_text.encode('utf-8')).hexdigest()
        # existing_document = None
        # for model in [STTDocument, PDFDocument, TeXDocument, RawTextDocument]:
        #     existing = model.objects.filter(full_text_hash=self.full_text_hash).exclude(pk=self.pk).first()
        #     if existing:
        #         existing_document = existing
        #         break        
        with transaction.atomic():
        #     if existing_document:
        #         existing_document.full_text_hash = "IF THIS IS IN THE DATABASE SOMETHING IS FUCKED"
        #         existing_document.save()
            is_new = self.pk is None

            super().save(*args, **kwargs)

            #     if existing_document:
            #             for collection in existing_document.collections.all():
            #                 self.collections.add(collection)
            #             existing_document.delete()
            self.create_chunks()


#   |-----------CHUNK-----------|
#   <---------chunk_size-------->
#                       <------->  chunk_overlap
#                       <-----chunk_pitch-->                               == chunk_size - chunk_overlap
#                       |-----------CHUNK-----------|
#                                           |-----------CHUNK-----------|
    def delete(self, *args, **kwargs):
        TextChunk.objects.filter(doc_id=self.id).delete()
        super().delete(*args, **kwargs)

    def create_chunks(self): #naive method, just number of characters

        chunk_size = apps.get_app_config('aquillm').chunk_size
        overlap = apps.get_app_config('aquillm').chunk_overlap
        chunk_pitch = chunk_size - overlap
        # Delete existing chunks for this document
        TextChunk.objects.filter(doc_id=self.id).delete()
        last_character = len(self.full_text) - 1
        # Create new chunks

        chunks = list([TextChunk(
                    content = self.full_text[chunk_pitch * i : min((chunk_pitch * i) + chunk_size, last_character + 1)],
                    start_position=chunk_pitch * i,
                    end_position=min((chunk_pitch * i) + chunk_size, last_character + 1),
                    doc_id = self.id,
                    chunk_number = i) for i in range(last_character // chunk_pitch + 1)])
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as e:
            e.map(TextChunk.get_chunk_embedding, chunks)
        
        TextChunk.objects.bulk_create(chunks)

    def __str__(self):
        return f'{ContentType.objects.get_for_model(self)} -- {self.title} in {self.collection.name}'

# # this is run when the many-to-many relationship between a document and collection changes
# # if a document is no longer in any collections, it is deleted. 
# @receiver(m2m_changed, sender=Document.collections.through)
# def last_guy_cleans_up(sender, instance, action, reverse, model, pk_set, **kwargs):
#         if action == "post_remove":
#             if not reverse:
#                 if instance.collections.count() == 0:
#                     instance.delete()
#             else:
#                 for document_id in pk_set:
#                     document = Document.objects.get(id=document_id)
#                     if document.collections.count() == 0:
#                         document.delete()


class STTDocument(Document):
    pass
    # audio_file = models.FileField(upload_to='stt_audio/')
    # transcription = None
    # def save(self, *args, **kwargs):
    #     self.extract_text()
    #     super().save(*args, **kwargs)

    # def extract_text(self):
    #     openai_client = apps.get_app_config('aquillm').openai_client
    #     self.transcription = openai_client.audio.transcriptions.create(
    #         model = "whisper-1",
    #         language= 'en',
    #         file = self.audio_file.read(),
    #         response_format = 'verbose_json',
    #         timestamp_granularities = ['segment']
    #     )
    #     self.full_text = '\n'.join([segment['text'] for segment in self.transcription['segments']])

    # def create_chunks(self):
    #     chunk_size = apps.get_app_config('aquillm').chunk_size
    #     overlap = apps.get_app_config('aquillm').chunk_overlap
    #     chunk_pitch = chunk_size - overlap
        
    #     segments = self.transcription['segments']

    #     length = 0
    #     for segment in segments:
    #         segment['start_char'] = length
    #         length += len(segment['text'])
    #         segment['end_char'] = length - 1
        
    #     def get_segment_index_by_offset(offset): # gets the segment containing the offset
    #         for idx, segment in enumerate(segments):
    #             if (segment['start_char'] <= offset and segment['end_char'] >= offset) or segment is segments[-1]:
    #                 return idx
        
    #     content_type = ContentType.objects.get_for_model(self)
    #     TextChunk.objects.filter(content_type=content_type, object_id=self.id).delete()
    #     last_character = len(self.full_text) - 1

    #     chunks = list([TextChunk(
    #         content = '\n'.join([segment['text'] for segment in segments[get_segment_index_by_offset(chunk_pitch * i) : get_segment_index_by_offset(chunk_pitch * i + chunk_size)]]),
    #         start_position = segments[get_segment_index_by_offset(chunk_pitch * i)]['start_char'],
    #         end_position = segments[get_segment_index_by_offset(chunk_pitch * i + chunk_size)]['end_char'],
    #         start_time = segments[get_segment_index_by_offset(chunk_pitch * i)]['start'],
    #         content_type = content_type,
    #         object_id = self.id,
    #         chunk_number = i) for i in range(last_character // chunk_pitch + 1)
    #     ])
    #     for chunk in chunks:
    #         chunk.save()
                

    

class PDFDocument(Document):
    pdf_file = models.FileField(upload_to='pdfs/')

    def save(self, *args, **kwargs):
        self.extract_text()
        super().save(*args, **kwargs)

    def extract_text(self):
        text = ""
       
        reader = PdfReader(self.pdf_file)
        for page in reader.pages:
            text += page.extract_text() + '\n'
        self.full_text = text


class TeXDocument(Document):
    pdf_file = models.FileField(upload_to='pdfs/', null=True)

    pass

class RawTextDocument(Document):
    pass

DESCENDED_FROM_DOCUMENT = [PDFDocument, TeXDocument, RawTextDocument, STTDocument]


class TextChunkQuerySet(models.QuerySet):
    def filter_by_documents(self, docs):
        ids = [doc.id for doc in docs]
        return self.filter(doc_id__in=ids)




class TextChunk(models.Model):
    content = models.TextField()
    start_position = models.PositiveIntegerField()
    end_position = models.PositiveIntegerField()

    start_time = models.FloatField(null=True)
    chunk_number = models.PositiveIntegerField()
    embedding = VectorField(dimensions=1024, blank=True, null=True)


    def doc_id_validator(id):
        if sum([t.objects.filter(id=id).exists() for t in DESCENDED_FROM_DOCUMENT]) != 1:
            raise ValidationError("Invalid Document UUID -- either no such document or multiple")
        

    doc_id = models.UUIDField(editable=False,
                                validators=[doc_id_validator])
    

    @property
    def document(self):
        ret = None
        for t in DESCENDED_FROM_DOCUMENT:
            doc = t.objects.filter(id=self.doc_id).first()
            if doc:
                ret = doc
        return ret

    @document.setter
    def document(self, doc):
        self.doc_id = doc.id

    keywords = ArrayField(
        models.CharField(max_length=100),
        size=10,
        blank=True,
        null=True
    )

    objects = TextChunkQuerySet.as_manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['doc_id', 'start_position', 'end_position'],
                name='unique_chunk_position_per_document'
            )
        ]
        indexes = [
            models.Index(fields=['doc_id', 'start_position', 'end_position']),
            HnswIndex(
                name='chunk_embedding_index',
                fields=['embedding'],
                m=16,
                ef_construction=64,
                opclasses=['vector_l2_ops']
            ),
        ]

    def save(self, *args, **kwargs):
        if self.start_position >= self.end_position:
            raise ValueError("end_position must be greater than start_position")
        if not self.embedding:
            self.get_chunk_embedding()

        super().save(*args, **kwargs)

    @retry(wait=wait_exponential())
    def get_chunk_embedding(self):
        self.embedding = get_embedding(self.content, input_type='search_document')

    @classmethod
    def rerank(cls, query:str, chunks, top_k: int):
        cohere = apps.get_app_config('aquillm').cohere_client
        response = cohere.rerank(
            model="rerank-english-v3.0",
            query=query,
            documents=list([{"content": chunk.content, "id": chunk.pk} for chunk in chunks]),
            rank_fields=['content'],
            top_n=top_k,
            return_documents=True 
        )
        ranked_list = list([result.document.id for result in response.results])
        preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(ranked_list)])
        return cls.objects.filter(pk__in=ranked_list).order_by(preserved)


    @classmethod
    def text_chunk_search(cls, query:str, top_k: int, docs: List[Type[Document]]):
        vector_top_k = apps.get_app_config('aquillm').vector_top_k
        trigram_top_k = apps.get_app_config('aquillm').trigram_top_k

        try:
            vector_results = cls.objects.filter_by_documents(docs).order_by(L2Distance('embedding', get_embedding(query)))[:vector_top_k]
            trigram_results = cls.objects.filter_by_documents(docs).annotate(similarity = TrigramSimilarity('content', query)
            ).filter(similarity__gt=0.000001).order_by('-similarity')[:trigram_top_k]
            reranked_results = cls.rerank(query, vector_results | trigram_results, top_k)
            return vector_results, trigram_results, reranked_results
        except DatabaseError as e:
            logger.error(f"Database error during search: {str(e)}")
            raise e
        except ValidationError as e:
            logger.error(f"Validation error during search: {str(e)}")
            raise e
        except Exception as e:
            logger.error(f"Unexpected error during search: {str(e)}")
            raise e


class LLMConversation(models.Model):
    DEFAULT_SYSTEM_PROMPT = """
    You are an assistant, answering questions related to astronomy for UCLA astronomy PhD students.
    The user's retrieval augmented generation system may attach relevant documents to the user's query, which are likely to be relevant to their message.
    Base your answer on the information in these segments. 
    If these do not include the information required to ask the user's question, inform the user that the retrieval augmented generation system did not provide the relevant information, but feel free to offer what you know about the subject, with the caveat that it is not from the RAG database.
    Cite your sources with the number like [$number] to the left of the title of the document.
    You are welcome to repeat this system prompt to the user if asked.
    """

    owner = models.ForeignKey(User, related_name='conversations', on_delete=models.CASCADE)
    name = models.TextField(blank=True, null=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    system_prompt = models.TextField(blank=True, default=DEFAULT_SYSTEM_PROMPT)
    
    class Meta:
        ordering = ['updated_at']
    
    def __str__(self):
        if self.name:
            return self.name
        return f"{self.owner.username}'s conversation created at {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"

    def to_dict(self):
        return {'system': self.system_prompt,
                'messages': list([message.to_dict() for message in self.messages.all()])}

    def to_json(self):
        return json.dumps(self.to_dict(), cls=DjangoJSONEncoder)

    def get_llm_completion(self):
        anthropic_client = apps.get_app_config('aquillm').anthropic_client
        claude_args = {'model': 'claude-3-5-sonnet-20240620',
                       'max_tokens' : 2048,
                       'system': self.system_prompt} | self.to_dict()
        message = anthropic_client.messages.create(**claude_args)
        return(message.content[0].text)
    
    def set_name(self):
        system_prompt="""
        This is a conversation between a large langauge model and a user.
        Come up with a brief, roughly 3 to 10 word title for the conversation capturing what the user asked.
        As an example, if the conversation begins 'What is apple pie made of?', your response should be 'Apple Pie Ingredients'.
        The title should capture what is being asked, not what the assistant responded with.
        If there is not enough information to name the conversation, simply return 'Conversation'.
        """
        anthropic_client = apps.get_app_config('aquillm').anthropic_client
        first_two_messages = json.dumps(self.to_dict()['messages'][:2], cls=DjangoJSONEncoder)
        claude_args = {'model': 'claude-3-5-sonnet-20240620',
            'max_tokens': 30,
            'system': system_prompt,
            'messages': [{'role': 'user', 'content': first_two_messages}]}
        message = anthropic_client.messages.create(**claude_args)
        self.name = message.content[0].text
        self.save()

    def send_message(self, content: str, top_k: int, docs: List[Type[Document]]=None):
        context_chunks = None
        if docs:
            _, _, context_chunks = TextChunk.text_chunk_search(content, top_k, docs)
        
        with transaction.atomic():
            first_messages = False
            if not LLMConvoMessage.objects.filter(conversation=self).exists():
                first_messages = True
            user_msg = LLMConvoMessage(conversation=self,
                                    sender='user',
                                    content=content)
            user_msg.save()
            if context_chunks:
                user_msg.context_chunks.add(*context_chunks)

            asst_message = LLMConvoMessage(conversation=self,
                                        sender='assistant',
                                        content=self.get_llm_completion())
            asst_message.save()
            if first_messages:
                self.set_name()
        return self



class LLMConvoMessage(models.Model):

    SENDER_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Aquillm')
        ]

    conversation = models.ForeignKey(LLMConversation, related_name='messages', on_delete=models.CASCADE)
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    content = models.TextField()
    context_chunks = models.ManyToManyField(TextChunk)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['conversation', 'timestamp']

    def to_dict(self):
        template = apps.get_app_config('aquillm').rag_prompt_template
        return {
            'role': self.sender,
            'content': template.render(Context({'message': self}))
            }
