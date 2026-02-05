from django import forms
from django.core.exceptions import ValidationError
from django.forms import modelformset_factory
from .models import Opinion, TagCourse, TagPortfolio, CategoryCourse, Course, Subject, Portfolio, Link, User, Transmition, Comment

class TransmitionForm(forms.ModelForm):
    participants = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.CheckboxSelectMultiple,  # albo SelectMultiple
        label="Wybierz uczestników"
    )

    class Meta:
        model = Transmition
        fields = ['title', 'description', 'participants', 'start', 'end']
        widgets = {
            'start': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['description']

class OpinionForm(forms.ModelForm):
    class Meta:
        model = Opinion
        fields = ['description'] 

class CourseForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=CategoryCourse.objects.all(),
        widget=forms.Select  # lub np. forms.RadioSelect
    )
    tags_select = forms.ModelMultipleChoiceField(
        queryset=TagCourse.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )

    tags_input = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Wpisz nowe tagi, oddzielone przecinkami'
        })
    )

    class Meta:
        model = Course
        fields = ['title', 'category']

    def clean_tags_input(self):
        input_tags = self.cleaned_data.get('tags_input', '')
        tag_names = [t.strip() for t in input_tags.split(',') if t.strip()]
        errors = []

        for name in tag_names:
            if TagCourse.objects.filter(name__iexact=name).exists():
                errors.append(f"Tag '{name}' już istnieje. Wybierz go z listy zamiast wpisywać.")

        if errors:
            raise ValidationError(errors)

        return tag_names  # lista stringów, używana później w save()

    def save(self, commit=True):
        offer = super().save(commit=False)
        if commit:
            offer.save()

        offer.tags.clear()

        # dodanie tagów z listy
        for tag in self.cleaned_data.get('tags_select', []):
            offer.tags.add(tag)

        # dodanie nowych tagów (przeszły już walidację)
        new_tag_names = self.cleaned_data.get('tags_input', [])
        for name in new_tag_names:
            tag = TagCourse.objects.create(name=name)
            offer.tags.add(tag)

        return offer

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['title', 'description', 'file']

SubjectFormSet = modelformset_factory(
    Subject,
    fields=['title', 'description', 'file'],
    extra=1,   # startowo 1 pusty formularz
    can_delete=True  # pozwala usuwać formularze
)

LinkFormSet = modelformset_factory(
    Link,
    fields=['url'],
    extra=1,   # startowo 1 pusty formularz
    can_delete=True  # pozwala usuwać formularze
)

class PortfolioForm(forms.ModelForm):
    tags_select = forms.ModelMultipleChoiceField(
        queryset=TagPortfolio.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )

    tags_input = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'placeholder': 'Wpisz nowe tagi, oddzielone przecinkami'
        })
    )

    class Meta:
        model = Portfolio
        fields = ['title']

    def clean_tags_input(self):
        input_tags = self.cleaned_data.get('tags_input', '')
        tag_names = [t.strip() for t in input_tags.split(',') if t.strip()]
        errors = []

        for name in tag_names:
            if TagPortfolio.objects.filter(name__iexact=name).exists():
                errors.append(f"Tag '{name}' już istnieje. Wybierz go z listy zamiast wpisywać.")

        if errors:
            raise ValidationError(errors)

        return tag_names  # lista stringów, używana później w save()

    def save(self, commit=True):
        offer = super().save(commit=False)
        if commit:
            offer.save()

        offer.tags.clear()

        # dodanie tagów z listy
        for tag in self.cleaned_data.get('tags_select', []):
            offer.tags.add(tag)

        # dodanie nowych tagów (przeszły już walidację)
        new_tag_names = self.cleaned_data.get('tags_input', [])
        for name in new_tag_names:
            tag = TagPortfolio.objects.create(name=name)
            offer.tags.add(tag)

        return offer

class LinkForm(forms.ModelForm):
    class Meta:
        model = Link
        fields = ['url']
