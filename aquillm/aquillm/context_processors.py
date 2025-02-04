def nav_links(request):
    return {
        'nav_links': [
            {"url": "new_ws_convo", "text": "New Conversation"},
            {"url": "user_ws_convos", "text": "Old Conversations"},
            {"url": "search", "text": "Search"},
            {"url": "collection_tree", "text": "Collections"},
            {"url": "insert_arxiv", "text": "Ingest from arXiv"},
            {"url": "ingest_pdf", "text": "Ingest PDF"},
            {"url": "ingest_vtt", "text": "Ingest Transcript"}
        ]
    }