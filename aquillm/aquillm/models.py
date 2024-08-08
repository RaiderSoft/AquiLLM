from django.db import models, transaction
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from pgvector.django import VectorField
from django.apps import apps
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.contrib.auth.models import User
from pypdf import PdfReader

from django.db.models import Q
import functools 
# for deleting documents when they are removed from the last collection they are in. 
from django.dispatch import receiver
from django.db.models.signals import m2m_changed

# for hashing full_text of documents to ensure unique contents
import hashlib


from io import BytesIO


class CollectionQuerySet(models.QuerySet):
    def filter_by_user_perm(self, user, perm='VIEW'):
        perm_options = []
        if perm == 'VIEW':
            perm_options = ['VIEW', 'EDIT', 'MANAGE']
        elif perm == 'EDIT':
            perm_options = ['EDIT', 'MANAGE'],
        elif perm == 'MANAGE':
            perm_options == ['MANAGE']
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
            


class Document(models.Model):


    title = models.CharField(max_length=200)
    full_text = models.TextField()
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    full_text_hash = models.CharField(max_length=64, db_index=True)

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

            super().save(*args, **kwargs)

            #     if existing_document:
            #             for collection in existing_document.collections.all():
            #                 self.collections.add(collection)
            #             existing_document.delete()

            is_new = self.pk is None
            if is_new or 'full_text' in kwargs.get('update_fields', []):
                self.create_chunks()


#   |-----------CHUNK-----------|
#   <---------chunk_size-------->
#                       <------->  chunk_overlap
#                       <-----chunk_pitch-->                               == chunk_size - chunk_overlap
#                       |-----------CHUNK-----------|
#                                           |-----------CHUNK-----------|
    

    def create_chunks(self): #naive method, just number of characters

        chunk_size = apps.get_app_config('aquillm').chunk_size
        overlap = apps.get_app_config('aquillm').chunk_overlap
        chunk_pitch = chunk_size - overlap
        # Delete existing chunks for this document
        content_type = ContentType.objects.get_for_model(self)
        TextChunk.objects.filter(content_type=content_type, object_id=self.id).delete()
        last_character = len(self.full_text) - 1
        # Create new chunks
        chunks = list([TextChunk(
                    content = self.full_text[chunk_pitch * i : min((chunk_pitch * i) + chunk_size, last_character + 1)],
                    start_position=chunk_pitch * i,
                    end_position=min((chunk_pitch * i) + chunk_size, last_character + 1),
                    content_type= content_type,
                    object_id = self.id,
                    chunk_number = i) for i in range(last_character // chunk_pitch + 1)])
        for chunk in chunks:
            chunk.save()

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
    audio_file = models.FileField(upload_to='stt_audio/')
    transcription = None
    def save(self, *args, **kwargs):
        self.extract_text()
        super().save(*args, **kwargs)

    def extract_text(self):
        openai_client = apps.get_app_config('aquillm').openai_client
        self.transcription = openai_client.audio.transcriptions.create(
            model = "whisper-1",
            language= 'en',
            file = self.audio_file.read(),
            response_format = 'verbose_json',
            timestamp_granularities = ['segment']
        )
        self.full_text = '\n'.join([segment['text'] for segment in self.transcription['segments']])

    def create_chunks(self):
        chunk_size = apps.get_app_config('aquillm').chunk_size
        overlap = apps.get_app_config('aquillm').chunk_overlap
        chunk_pitch = chunk_size - overlap
        
        segments = self.transcription['segments']

        length = 0
        for segment in segments:
            segment['start_char'] = length
            length += len(segment['text'])
            segment['end_char'] = length - 1
        
        def get_segment_index_by_offset(offset): # gets the segment containing the offset
            for idx, segment in enumerate(segments):
                if (segment['start_char'] <= offset and segment['end_char'] >= offset) or segment is segments[-1]:
                    return idx
        
        content_type = ContentType.objects.get_for_model(self)
        TextChunk.objects.filter(content_type=content_type, object_id=self.id).delete()
        last_character = len(self.full_text) - 1

        chunks = list([TextChunk(
            content = '\n'.join([segment['text'] for segment in segments[get_segment_index_by_offset(chunk_pitch * i) : get_segment_index_by_offset(chunk_pitch * i + chunk_size)]]),
            start_position = segments[get_segment_index_by_offset(chunk_pitch * i)]['start_char'],
            end_position = segments[get_segment_index_by_offset(chunk_pitch * i + chunk_size)]['end_char'],
            start_time = segments[get_segment_index_by_offset(chunk_pitch * i)]['start'],
            content_type = content_type,
            object_id = self.id,
            chunk_number = i) for i in range(last_character // chunk_pitch + 1)
        ])
        for chunk in chunks:
            chunk.save()
                

    

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
        hashes = [doc.full_text_hash for doc in docs]
        q = functools.reduce(lambda l, r: l | r, [Q(content_type=ContentType.objects.get_for_model(model),
                                                    object_id__in=model.objects.filter(full_text_hash__in=hashes).values_list('id', flat=True))
                                                    for model in DESCENDED_FROM_DOCUMENT])
        return self.filter(q)



class TextChunk(models.Model):
    content = models.TextField()
    start_position = models.PositiveIntegerField()
    end_position = models.PositiveIntegerField()

    start_time = models.FloatField(null=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    document = GenericForeignKey('content_type', 'object_id')
    
    chunk_number = models.PositiveIntegerField()

    keywords = ArrayField(
        models.CharField(max_length=100),
        size=10,
        blank=True,
        null=True
    )
    embedding = VectorField(dimensions=1024,blank=True, null=True)

    objects = TextChunkQuerySet.as_manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['content_type', 'object_id', 'start_position', 'end_position'],
                name='unique_chunk_position_per_document'
            )
        ]
        indexes = [
            models.Index(fields=['content_type', 'object_id', 'start_position', 'end_position'])
        ]

    def save(self, *args, **kwargs):
        if self.start_position >= self.end_position:
            raise ValueError("end_position must be greater than start_position")
        self.get_embedding()

        super().save(*args, **kwargs)

    
    def get_embedding(self):
        cohere = apps.get_app_config('aquillm').cohere_client
        response = cohere.embed(
            texts=[self.content], model="embed-english-v3.0", input_type="search_document"
        )
        self.embedding = response.embeddings[0]


