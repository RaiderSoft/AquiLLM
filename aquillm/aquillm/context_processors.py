from .models import WSConversation

def nav_links(request):
    return {
        'nav_links': [
            {"url": "new_ws_convo", "text": "New Conversation"},
            {"url": "user_ws_convos", "text": "Old Conversations"},
            {"url": "search", "text": "Search"},
            {"url": "folder_app", "text": "Collections"},
            {"url": "insert_arxiv", "text": "Ingest from arXiv"},
            {"url": "ingest_pdf", "text": "Ingest PDF"},
            {"url": "ingest_vtt", "text": "Ingest Transcript"}
        ]
    }

def user_conversations(request):
    if request.user.is_authenticated:
        convos = WSConversation.objects.filter(owner=request.user).order_by('-updated_at')
        return {'conversations': convos}
    return {}