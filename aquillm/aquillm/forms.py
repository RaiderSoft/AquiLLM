from django import forms
from .models import Collection, CollectionPermission, PDFDocument
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

User = get_user_model()


class UserCollectionMultipleChoiceField(forms.ModelMultipleChoiceField):
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.queryset = self._get_queryset()
        self.initial = self._get_queryset()

    def _get_queryset(self):
        return Collection.objects.filter(
            pk__in=[perm.collection.id for perm in CollectionPermission.objects.filter(user=self.user).distinct()]
        )
    
class UserCollectionSingleChoiceField(forms.ModelChoiceField):
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.queryset = self._get_queryset()

    def _get_queryset(self):
        return Collection.objects.filter(
            pk__in=[perm.collection.id for perm in CollectionPermission.objects.filter(user=self.user).distinct()]
        )
    

class NewCollectionForm(forms.Form):
    name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    viewers = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-control'}),
    )
    
    editors = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-control'}),
    )
    
    admins = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-control'}),
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            qs = User.objects.exclude(id=user.id)
            self.fields['viewers'].queryset = qs
            self.fields['editors'].queryset = qs
            self.fields['admins'].queryset = qs

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data['editors'] = cleaned_data['editors'].exclude(pk__in=cleaned_data['admins'])
        cleaned_data['viewers'] = cleaned_data['viewers'].exclude(pk__in=cleaned_data['editors'])
        cleaned_data['viewers'] = cleaned_data['viewers'].exclude(pk__in=cleaned_data['admins'])

        return cleaned_data

class SearchForm(forms.Form):
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)

        collections_attrs = {
            'class': 'rounded-lg bg-gray-shade_3 mb-4 max-h-[300px] overflow-y-auto px-4 py-2 border border-gray-shade_7',
        }
        self.fields['collections'] = UserCollectionMultipleChoiceField(
            user=user,
            widget=forms.CheckboxSelectMultiple(attrs=collections_attrs),
            queryset=Collection.objects.none(), # this is weird but necessary
            required=False,
        )

    query_attrs = {
        'class': 'w-full h-full resize-none p-3 mb-4 rounded-md bg-gray-shade_3 placeholder:text-gray-shade_a text-wrap text-gray-shade_e',
        'rows': 4,
        'placeholder': 'Send a message'}
    
    query = forms.CharField(label="Query", widget=forms.Textarea(attrs=query_attrs), max_length=10000)

    top_k_attrs = {
        'class': 'w-full p-2 rounded-md bg-gray-shade_3 placeholder:text-gray-shade_9 text-gray-shade_e mb-4',
    }

    top_k = forms.IntegerField(widget=forms.NumberInput(attrs=top_k_attrs), min_value=1, max_value=200, initial=5)


class ArXiVForm(forms.Form):
    arxiv_id = forms.CharField(
        label="Article arXiv Identifier",  
        widget=forms.TextInput(attrs={
            'placeholder': 'Article arXiv Identifier:', 
            'class': 'rounded-[8px] w-full p-2 bg-gray-shade_4 border border-gray-shade_7 placeholder:gray-shade_9' 
        })
    )

    collection = forms.ChoiceField(widget=forms.RadioSelect)

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['collection'].choices = [(col.id, col.name) for col in Collection.objects.filter_by_user_perm(user, perm="EDIT")]


class PDFDocumentForm(forms.Form):
    title = forms.CharField(
        label="Article Title",  
        widget=forms.TextInput(attrs={
            'placeholder': 'Article Title:', 
            'class': 'rounded-[8px] w-full p-2 bg-gray-shade_4 border border-gray-shade_7 placeholder:gray-shade_9' 
        })
    )

    pdf_file = forms.FileField(
        label="PDF File",
        widget=forms.ClearableFileInput(attrs={
            'class': 'hidden',  # hide the default file input
            'id': 'pdf-file-input'  # assign an ID for linking the custom label
        })
    )

    # TODO: make function sig not weird
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        collections_attrs = {
           'class': 'rounded-md bg-lightest-primary',
        }
        self.fields['collection'] = UserCollectionSingleChoiceField(
            user=user,
            widget=forms.RadioSelect(attrs=collections_attrs),
            queryset=Collection.objects.none(), # this is weird but necessary
            required=True,
        )
    
class VTTDocumentForm(forms.Form):
    title = forms.CharField(
        label="Transcript Title",  
        widget=forms.TextInput(attrs={
            'placeholder': 'Transcript Title:', 
            'class': 'rounded-[8px] w-full p-2 bg-gray-shade_4 border border-gray-shade_7 placeholder:gray-shade_9' 
        })
    )

    vtt_file = forms.FileField(
        label="Audio File (optional)",
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'class': 'hidden',
            'id': 'audio-file-input'
        })
    )

    vtt_file = forms.FileField(
        label=".vtt Transcript File",
        widget=forms.ClearableFileInput(attrs={
            'class': 'hidden',
            'id': 'vtt-file-input'
        })
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        collections_attrs = {
           'class': 'rounded-md bg-lightest-primary',
        }
        self.fields['collection'] = UserCollectionSingleChoiceField(
            user=user,
            widget=forms.RadioSelect(attrs=collections_attrs),
            queryset=Collection.objects.none(), # this is weird but necessary
            required=True,
        )