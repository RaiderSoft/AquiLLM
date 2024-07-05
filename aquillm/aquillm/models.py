from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from pgvector.django import VectorField
from django.apps import apps






class Document(models.Model):
    title = models.CharField(max_length=200)
    full_text = models.TextField()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new or 'full_text' in kwargs.get('update_fields', []):
            self.create_chunks()


    def create_chunks(self):
        # Delete existing chunks for this document
        content_type = ContentType.objects.get_for_model(self)
        TextChunk.objects.filter(content_type=content_type, object_id=self.id).delete()

        # Create new chunks
        start = 0
        while start < len(self.full_text):
            end = start + self.chunk_size

            if end > len(self.full_text):
                end = len(self.full_text)
            else:
                # Try to find a space to break at
                while end > start and self.full_text[end] != ' ':
                    end -= 1
                if end == start:
                    end = start + self.chunk_size  # If no space found, just break at chunk_size

            TextChunk.objects.create(
                content_type=content_type,
                object_id=self.id,
                content=self.full_text[start:end],
                start_position=start,
                end_position=end
            )

            # Move start for next chunk, incorporating overlap
            start = end - self.chunk_overlap
            if start < 0:
                start = 0
            
            # Find the next word start if we're not at the beginning
            if start > 0:
                while start < len(self.full_text) and self.full_text[start] != ' ':
                    start += 1
                start += 1  # move past the space
            
            if start >= len(self.full_text):
                break  # Exit if we've reached the end of the text
class STTDocument(Document):
    audio_file = models.FileField(upload_to='stt_audio/')

class PDFDocument(Document):
    pdf_file = models.FileField(upload_to='pdfs/')

class TeXDocument(Document):
    pass

class RawTextDocument(Document):
    pass

class TextChunk(models.Model):
    content = models.TextField()
    start_position = models.PositiveIntegerField()
    end_position = models.PositiveIntegerField()

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    document = GenericForeignKey('content_type', 'object_id')
    
    keywords = ArrayField(
        models.CharField(max_length=100),
        size=10,
        blank=True,
        null=True
    )
    embedding = VectorField(dimensions=1024)

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
        
        if not self.embedding:
            self.get_embedding()

        super().save(*args, **kwargs)

    
    def get_embedding(self):
        cohere = apps.get_app_config('aquillm').cohere_client
        response = cohere.embed(
            texts=[self.content], model="embed-english-v3.0", input_type="search_document"
        )
        self.embedding = response.embeddings[0]
