from django import forms
from .models import Collection, CollectionPermission

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
    


class SearchForm(forms.Form):
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['collections'] = UserCollectionMultipleChoiceField(
            user=user,
            widget=forms.CheckboxSelectMultiple,
            queryset=Collection.objects.none() # this is weird but necessary
        )
    query = forms.CharField(label="Search Query", max_length=10000)
    top_k = forms.IntegerField(min_value=1, max_value=200, initial=5)


class ArXiVForm(forms.Form):
    arxiv_id = forms.CharField(label="Article arXiv Identifier", max_length=100)
