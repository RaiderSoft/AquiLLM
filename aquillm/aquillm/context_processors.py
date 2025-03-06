from .models import WSConversation
from django.urls import get_resolver
def nav_links(request):
    return {
        'nav_links': [
            {"url": "new_ws_convo", "text": "New Conversation"},
            {"url": "user_ws_convos", "text": "Old Conversations"},
            {"url": "search", "text": "Search"},
            {"url": "user_collections", "text": "Collections"},

        ]
    }
resolver=get_resolver()
_api_url_dict = {key: "/" + url_pattern[0][0][0] for key, url_pattern in resolver.reverse_dict.items() if url_pattern[0][0][0].split('/')[0] == 'api' and isinstance(key, str)} # type: ignore
_page_url_dict = {key: "/" + url_pattern[0][0][0] for key, url_pattern in resolver.reverse_dict.items() if url_pattern[0][0][0].split('/')[0] != 'api' and isinstance(key, str)} # type: ignore

def api_urls(request):
    return {'api_urls': _api_url_dict}

def page_urls(request):
    return {'page_urls': _page_url_dict}

def user_conversations(request):
    if request.user.is_authenticated:
        convos = WSConversation.objects.filter(owner=request.user).order_by('-updated_at')
        return {'conversations': convos}
    return {}