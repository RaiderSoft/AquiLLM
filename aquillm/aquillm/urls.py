"""
URL configuration for aquillm project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include, re_path
from django.contrib.auth import views as auth_views
from debug_toolbar.toolbar import debug_toolbar_urls
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

from chat import views as chat_views
from . import views
from .settings import DEBUG

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', views.index, name='index'),
    path('accounts/', include('allauth.urls')),
    
    # API endpoints
    path("api/collections/", views.get_collections_json, name="get_collections_json"),
    path("api/collections/delete/<int:collection_id>/", views.delete_collection, name="delete_collection"),
    
    # React app specific routes - redirect old URLs to React app versions
    path('collections/', lambda request: redirect('/app/collections/')),
    path('collections/<path:path>', lambda request, path: redirect(f'/app/collections/{path}')),
    path('chat/', lambda request: redirect('/app/chat/')),
    
    # React app route handler - only for specific paths
    re_path(r'^app/(collections|chat)/.*$', TemplateView.as_view(template_name='index.html')),
    
    # Original Django routes
    path("search/", views.search, name='search'),
    path("insert_arxiv/", views.insert_arxiv, name='insert_arxiv'),
    path('user_conversations/', views.user_conversations, name="user_conversations"),
    path("raw_convo/<int:convo_id>/", views.raw_convo, name="raw_convo"),
    path("convo/<int:convo_id>/", views.convo, name="convo"),
    path("new_convo/", views.new_convo, name="new_convo"),
    path("send_message/<int:convo_id>/", views.send_message, name="send_message"),
    path("pdf/<uuid:doc_id>/", views.pdf, name="pdf"),
    path("document/<uuid:doc_id>/", views.document, name="document"),
    path("move_document/<uuid:doc_id>/", views.move_document, name="move_document"),
    path("user_collections/", views.user_collections, name="user_collections"),
    path("collection/<int:col_id>/", views.collection, name="collection"),
    path("collection/<int:col_id>/permissions/", views.update_collection_permissions, name="update_collection_permissions"),
    path("ingest_pdf/", views.ingest_pdf, name="ingest_pdf"),
    path("ingest_vtt/", views.ingest_vtt, name="ingest_vtt"),
    path("delete_document/<uuid:doc_id>", views.delete_document, name="delete_document"),
    path("ws_convo/<int:convo_id>/", views.ws_convo, name="ws_convo"),
    path("user_ws_convos/", views.user_ws_convos, name="user_ws_convos"),
    path("new_ws_convo/", chat_views.new_ws_convo, name="new_ws_convo"),
    path("delete_ws_convo/<int:convo_id>", views.delete_ws_convo, name="delete_ws_convo"),
    path("health/", views.health_check, name="health"),
    path("ready/", views.health_check, name="ready"),
    path("health", views.health_check),
    path("ready", views.health_check),
    path("react_test", views.react_test, name="react_test"),
    path('collections/', views.collection_tree, name='collection_tree'),
    path('collections/create/', views.create_collection, name='create_collection'),
    path('collections/create/<int:parent_id>/', views.create_collection, name='create_collection_under_parent'),
    path('collections/<int:collection_id>/', views.collection_detail, name='collection_detail'),
    path('collections/<int:collection_id>/move/', views.move_collection, name='move_collection'),
    path('documents/<uuid:doc_id>/move/', views.move_document, name='move_document'),
] + debug_toolbar_urls()

if DEBUG:
   urlpatterns += [path("debug_models/", views.debug_models, name="debug_models")]

# Catch-all route to serve the React app's index.html for all non-API URLs.
# This allows React Router to handle client-side routing.
urlpatterns += [
    re_path(r'^(?!api/).*$', TemplateView.as_view(template_name='index.html'))
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 