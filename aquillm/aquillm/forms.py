from django import forms
from .models import Collection, CollectionPermission, PDFDocument
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from .models import HandwrittenNotesDocument, Collection

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

class HandwrittenNotesForm(forms.Form):
    """
    Form for uploading handwritten notes with optional LaTeX conversion.
    
    This form allows users to:
    1. Upload an image file containing handwritten notes
    2. Specify a title for the document
    3. Select a collection to store it in
    4. Optionally request LaTeX conversion for mathematical expressions
    """
    
    # Basic document metadata
    title = forms.CharField(
        label="Handwritten Notes Title",
        help_text="Give your notes a descriptive title"
    )
    
    # The image file containing handwritten notes
    image_file = forms.ImageField(
        label="Handwritten Notes File",
        help_text="Upload a PNG, JPG, or JPEG image of your handwritten notes"
    )
    
    # Optional LaTeX conversion checkbox
    convert_to_latex = forms.BooleanField(
        label="Convert to LaTeX",
        required=False, 
        help_text="Convert mathematical expressions to properly rendered LaTeX format"
    )

    class Meta:
        # Link to the model for form generation
        model = HandwrittenNotesDocument
        fields = ['title', 'image_file', 'collection', 'convert_to_latex']

    def __init__(self, user, *args, **kwargs):
        """
        Initialize the form with user-specific collections.
        
        Args:
            user: The current authenticated user
            *args, **kwargs: Standard form initialization arguments
        """
        super().__init__(*args, **kwargs)
        
        # Style the collection selection widgets
        collections_attrs = {
           'class': 'rounded-md bg-lightest-primary',
        }
        
        # Add the collection field dynamically based on user
        # This shows only collections the user has access to
        self.fields['collection'] = UserCollectionSingleChoiceField(
            user=user,
            widget=forms.RadioSelect(attrs=collections_attrs),
            queryset=Collection.objects.none(),  # Will be set by the field's __init__
            required=True,
        )
