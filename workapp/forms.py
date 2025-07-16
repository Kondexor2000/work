from django import forms
from django.core.exceptions import ValidationError
from django.forms import modelformset_factory
from .models import CV, HR, Business, TagBusiness, TagCourse, TagPortfolio, Test, CategoryCourse, CategoryEmploy, OffersJob,OffersJobUser, Course, Subject, Questions, Answers, Portfolio, Projects, Link, Experience, User, Hobby, Skills, Questionnaire, Education

class CVForm(forms.ModelForm):
    class Meta:
        model = CV
        fields = ['title', 'first_name', 'last_name', 'email', 'number_phone']  # Zmieniono: 'e-mail' → 'email'

class HRForm(forms.ModelForm):
    class Meta:
        model = HR
        fields = ['first_name', 'last_name', 'email', 'number_phone', 'business']  # 'e-mail' → 'email'

class BusinessForm(forms.ModelForm):
    class Meta:
        model = Business
        fields = ['name']

class OfferJobsForm(forms.ModelForm):
    tags_select = forms.ModelMultipleChoiceField(
        queryset=TagBusiness.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )

    tags_input = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Wpisz nowe tagi, oddzielone przecinkami'
        })
    )

    category = forms.ModelChoiceField(
        queryset=CategoryEmploy.objects.all(),
        widget=forms.Select
    )

    class Meta:
        model = OffersJob
        fields = ['title', 'category', 'file']  # tags nie jest bezpośrednio w Meta

    def clean_tags_input(self):
        input_tags = self.cleaned_data.get('tags_input', '')
        tag_names = [t.strip() for t in input_tags.split(',') if t.strip()]
        errors = []

        for name in tag_names:
            if TagBusiness.objects.filter(name__iexact=name).exists():
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
            tag = TagBusiness.objects.create(name=name)
            offer.tags.add(tag)

        return offer

class UpdateOfferJobUserForm(forms.ModelForm):
    class Meta:
        model = OffersJobUser
        fields = ['is_accept']

class AddOfferJobUserForm(forms.ModelForm):
    user = forms.ModelChoiceField(queryset=User.objects.all(), label="Wyślij zaproszenie do")

    class Meta:
        model = OffersJobUser
        fields = ['user']

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

class TestForm(forms.ModelForm):
    class Meta:
        model = Test
        fields = ['title', 'is_finish']

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Questions
        fields = ['question', 'correct']

QuestionFormSet = modelformset_factory(
    Questions,
    fields=['question', 'correct'],
    extra=1,   # startowo 1 pusty formularz
    can_delete=True  # pozwala usuwać formularze
)

SubjectFormSet = modelformset_factory(
    Subject,
    fields=['title', 'description', 'file'],
    extra=1,   # startowo 1 pusty formularz
    can_delete=True  # pozwala usuwać formularze
)

ProjectsFormSet = modelformset_factory(
    Projects,
    fields=['title', 'file'],
    extra=1,   # startowo 1 pusty formularz
    can_delete=True  # pozwala usuwać formularze
)

LinkFormSet = modelformset_factory(
    Link,
    fields=['url'],
    extra=1,   # startowo 1 pusty formularz
    can_delete=True  # pozwala usuwać formularze
)

ExperienceFormSet = modelformset_factory(
    Experience,
    fields=['company', 'position'],
    extra=1,   # startowo 1 pusty formularz
    can_delete=True  # pozwala usuwać formularze
)

SkillsFormSet = modelformset_factory(
    Skills,
    fields=['skill'],
    extra=1,   # startowo 1 pusty formularz
    can_delete=True  # pozwala usuwać formularze
)

HobbyFormSet = modelformset_factory(
    Hobby,
    fields=['hobby'],
    extra=1,   # startowo 1 pusty formularz
    can_delete=True  # pozwala usuwać formularze
)

EducationFormSet = modelformset_factory(
    Education,
    fields=['fields_of_state', 'place'],
    extra=1,   # startowo 1 pusty formularz
    can_delete=True  # pozwala usuwać formularze
)

class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answers
        fields = ['answer']

class PortfolioForm(forms.ModelForm):
    tags_select = forms.ModelMultipleChoiceField(
        queryset=TagPortfolio.objects.all(),
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

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Projects
        fields = ['title', 'file']

class LinkForm(forms.ModelForm):
    class Meta:
        model = Link
        fields = ['url']

class ExperienceForm(forms.ModelForm):
    class Meta:
        model = Experience
        fields = ['company', 'position']

class HobbyForm(forms.ModelForm):
    class Meta:
        model = Hobby
        fields = ['hobby']

class EducationForm(forms.ModelForm):
    class Meta:
        model = Education
        fields = ['fields_of_state', 'place']

class SkillsForm(forms.ModelForm):
    class Meta:
        model = Skills
        fields = ['skill']

class QuestionnaireForm(forms.ModelForm):
    name = forms.ModelChoiceField(
            queryset=Questionnaire.objects.all(),
            widget=forms.Select
        )
    
    class Meta:
        model = Questionnaire
        fields = ['name']