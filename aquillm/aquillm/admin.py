from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.urls import reverse
from django.utils.html import format_html
from .models import RawTextDocument, HandwrittenNotesDocument, PDFDocument, VTTDocument, TeXDocument, TextChunk, Collection, CollectionPermission, LLMConversation, LLMConvoMessage, WSConversation

# class TextChunkInline(GenericTabularInline):
#     model = TextChunk
#     extra = 0
#     readonly_fields = ('start_position', 'end_position', 'chunk_number', 'admin_link')
#     can_delete = False
#     max_num = 0
#     fields = ('admin_link', 'start_position', 'end_position', 'chunk_number')

#     def has_add_permission(self, request, obj):
#         return False


#     def admin_link(self, instance):
#         url = reverse('admin:aquillm_textchunk_change', args=[instance.id])
#         return format_html('<a href="{}">View Details</a>', url)
#     admin_link.short_description = 'Details'


@admin.register(VTTDocument)
@admin.register(TeXDocument)
@admin.register(PDFDocument)
@admin.register(HandwrittenNotesDocument)
@admin.register(RawTextDocument)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'id')
    search_fields = ('title', 'full_text')
    # inlines = [TextChunkInline]



@admin.register(TextChunk)
class TextChunkAdmin(admin.ModelAdmin):
    list_display = ('chunk_number', 'start_position', 'end_position', 'document', 'embedding')
    search_fields = ('content',)

@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(CollectionPermission)
class CollectionPermissionAdmin(admin.ModelAdmin):
    list_display = ('collection', 'user', 'permission')


@admin.register(LLMConversation)
class LLMConversationAdmin(admin.ModelAdmin):
    list_display = ('owner', 'created_at')

@admin.register(LLMConvoMessage)
class LLMConvoMessageAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'timestamp', 'sender')

@admin.register(WSConversation)
class WSConversationAdmin(admin.ModelAdmin):
    list_display = ('owner', 'id')