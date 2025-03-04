from django import forms
from .models import Collection, CollectionPermission, PDFDocument, HandwrittenNotesDocument
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
            'class': 'rounded-md bg-lightest-primary',
        }
        self.fields['collections'] = UserCollectionMultipleChoiceField(
            user=user,
            widget=forms.CheckboxSelectMultiple(attrs=collections_attrs),
            queryset=Collection.objects.none(), # this is weird but necessary
            required=False,
        )

    query_attrs = {
        'class': 'w-full h-full resize-none p-3 mb-3 rounded-md bg-lightest-primary text-wrap',
        'rows': 4,
        'placeholder': 'Send a message'}
    query = forms.CharField(label="", widget=forms.Textarea(attrs=query_attrs), max_length=10000)
    top_k_attrs = {
        'class': 'w-full m-2 p-2 rounded-md bg-lightest-primary'
    }
    top_k = forms.IntegerField(widget=forms.NumberInput(attrs=top_k_attrs), min_value=1, max_value=200, initial=5)


class ArXiVForm(forms.Form):
    collection = forms.ChoiceField(widget=forms.RadioSelect)
    arxiv_id = forms.CharField(label="Article arXiv Identifier", max_length=100)

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['collection'].choices = [(col.id, col.name) for col in Collection.objects.filter_by_user_perm(user, perm="EDIT")]


class PDFDocumentForm(forms.Form):
    title = forms.CharField(label="Article Title")
    pdf_file = forms.FileField(label="PDF File")
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
    title = forms.CharField(label="Transcript Title")
    audio_file = forms.FileField(label="Audio File (optional)", required=False)
    vtt_file = forms.FileField(label=".vtt Transcript File")
    


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

class HandwrittenNotesForm(forms.ModelForm):
    title = forms.CharField(label="Handwritten Notes Title")
    image_file = forms.ImageField(label=".png Handwritten Notes File")

    class Meta:
        model = HandwrittenNotesDocument
        fields = ['title', 'image_file', 'collection']

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
