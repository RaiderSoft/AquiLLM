from rest_framework import serializers
from aquillm.models import Folder, Collection

class FolderSerializer(serializers.ModelSerializer):
    path = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()
    document_count = serializers.SerializerMethodField()

    class Meta:
        model = Folder
        fields = ['id', 'name', 'parent', 'collection', 'path', 'children', 'document_count', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def get_path(self, obj):
        return obj.get_path()

    def get_children(self, obj):
        return FolderSerializer(obj.children.all(), many=True).data

    def get_document_count(self, obj):
        return obj.documents.count()

    def validate(self, data):
        # Ensure the parent folder belongs to the same collection
        if data.get('parent') and data['parent'].collection != data['collection']:
            raise serializers.ValidationError("Parent folder must belong to the same collection")
        return data 