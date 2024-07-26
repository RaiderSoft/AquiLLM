from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from pgvector.django import VectorField
from django.apps import apps
from django.core.exceptions import ValidationError

from pypdf import PdfReader
from io import BytesIO



class Document(models.Model):
    title = models.CharField(max_length=200)
    full_text = models.TextField()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if len(self.full_text) < 100:
            raise ValidationError("The full text of a document must be at least 100 characters long.")
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
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
