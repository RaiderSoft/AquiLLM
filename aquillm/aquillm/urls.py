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
from django.urls import path, include
from django.contrib.auth import views as auth_views
from debug_toolbar.toolbar import debug_toolbar_urls

from chat import views as chat_views
from . import views
from .settings import DEBUG

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', views.index, name='index'),
    path('accounts/', include('allauth.urls')),
    path("search/", views.search, name='search'),
    path("insert_arxiv/", views.insert_arxiv, name='insert_arxiv'),
    path('user_conversations/', views.user_conversations, name="user_conversations"),
    path("raw_convo/<int:convo_id>/", views.raw_convo, name="raw_convo"),
    path("convo/<int:convo_id>/", views.convo, name="convo"),
    path("new_convo/", views.new_convo, name="new_convo"),
    path("send_message/<int:convo_id>/", views.send_message, name="send_message"),
    path("pdf/<uuid:doc_id>/", views.pdf, name="pdf"),
    path("document/<uuid:doc_id>/", views.document, name="document"),
    path("user_collections/", views.user_collections, name="user_collections"),
    path("get_collections_json/", views.get_collections_json, name="get_collections_json"),
    path("collection/move/<int:collection_id>/", views.move_collection, name="move_collection"),
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
    path("pdf_ingestion_monitor/<int:doc_id>/", views.pdf_ingestion_monitor, name="pdf_ingestion_monitor"),
] + debug_toolbar_urls()

if DEBUG:
   urlpatterns += [path("debug_models/", views.debug_models, name="debug_models")] 