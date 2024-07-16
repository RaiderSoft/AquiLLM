from django import forms

class SearchForm(forms.Form):
    query = forms.CharField(label="Search Query", max_length=10000)
    top_k = forms.IntegerField(min_value=1, max_value=200, initial=5)
