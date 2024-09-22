

def nav_links(request):
    return {
        'nav_links': [
            {"url": "new_convo", "text": "New Conversation"},
            {"url": "user_conversations", "text": "Old Conversations"},
            {"url": "search", "text": "Search"},
            {"url": "user_collections", "text": "Collections"},
            {"url": "insert_arxiv", "text": "Ingest from arXiv"},
        ]
    }