from django.shortcuts import render, redirect
from aquillm.models import WSConversation 

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

# Create your views here.


@require_http_methods(['GET'])
@login_required
def new_ws_convo(request):
    convo = WSConversation(owner=request.user)
    convo.save()
    return redirect('ws_convo', convo_id=convo.id)

