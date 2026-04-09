from django import forms
from django.core.exceptions import ValidationError
from django.forms import modelformset_factory
from .models import TagPortfolio, Link

class LinkForm(forms.ModelForm):

    class Meta:
        model = Link
        fields = ['description', 'tags']

    def clean_description(self):
        desc = self.cleaned_data.get('description', '').strip()
        if not desc:
            raise ValidationError("To pole jest wymagane")
        return desc