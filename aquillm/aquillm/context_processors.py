def nav_links(request):
    return {
        'nav_links': [
            {"url": "new_ws_convo", "text": "New Conversation"},
            {"url": "user_ws_convos", "text": "Old Conversations"},
            {"url": "search", "text": "Search"},
            {"url": "user_collections", "text": "Collections"},
            {"url": "insert_arxiv", "text": "Ingest from arXiv"},
            {"url": "ingest_pdf", "text": "Ingest PDF"},
            {"url": "ingest_vtt", "text": "Ingest Transcript"},
            {"url": "ingest_handwritten_notes", "text": "Ingest Handwritten Notes"},
            {"url": "gemini_cost_monitor", "text": "Gemini Costs"}
        ]
    }