from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from aquillm.models import Folder, Collection, Document
from .serializers import FolderSerializer

class FolderViewSet(viewsets.ModelViewSet):
    serializer_class = FolderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only return folders from collections the user has access to
        return Folder.objects.filter(
            collection__in=Collection.objects.filter_by_user_perm(self.request.user)
        )

    def perform_create(self, serializer):
        collection = serializer.validated_data['collection']
        if not collection.user_can_edit(self.request.user):
            raise permissions.PermissionDenied("You don't have edit permission for this collection")
        serializer.save()

    @action(detail=True, methods=['post'])
    def move_documents(self, request, pk=None):
        folder = self.get_object()
        document_ids = request.data.get('document_ids', [])
        
        if not folder.collection.user_can_edit(request.user):
            return Response(
                {"detail": "You don't have permission to move documents in this collection"},
                status=status.HTTP_403_FORBIDDEN
            )

        documents = Document.objects.filter(
            id__in=document_ids,
            collection=folder.collection
        )

        documents.update(folder=folder)
        return Response({"status": "Documents moved successfully"})

    @action(detail=True, methods=['post'])
    def move_folder(self, request, pk=None):
        folder = self.get_object()
        new_parent_id = request.data.get('parent_id')
        
        if not folder.collection.user_can_edit(request.user):
            return Response(
                {"detail": "You don't have permission to move folders in this collection"},
                status=status.HTTP_403_FORBIDDEN
            )

        if new_parent_id:
            new_parent = get_object_or_404(Folder, id=new_parent_id)
            if new_parent.collection != folder.collection:
                return Response(
                    {"detail": "Cannot move folder to a different collection"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            folder.parent = new_parent
        else:
            folder.parent = None
        
        folder.save()
        return Response(FolderSerializer(folder).data) 