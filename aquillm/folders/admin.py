from django.contrib import admin
from aquillm.models import Folder

@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    list_display = ('name', 'collection', 'parent', 'created_at', 'updated_at')
    list_filter = ('collection', 'created_at', 'updated_at')
    search_fields = ('name', 'collection__name')
    raw_id_fields = ('parent', 'collection') 