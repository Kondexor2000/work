from django import forms
from .models import CV, HR, Business, TagBusiness, TagCourse, TagPortfolio, Test, CategoryCourse, CategoryEmploy, OffersJob,OffersJobUser, Course, Subject, Questions, Answers, Portfolio, Projects, Link, Experience, User

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
    tags = forms.ModelMultipleChoiceField(
        queryset=TagBusiness.objects.all(),
        widget=forms.CheckboxSelectMultiple # lub inny widget, np. forms.SelectMultiple
    )
    category = forms.ModelMultipleChoiceField(
        queryset=CategoryEmploy.objects.all(),
        widget=forms.CheckboxSelectMultiple # lub inny widget, np. forms.SelectMultiple
    )

    class Meta:
        model = OffersJob
        fields = ['title', 'tags', 'category', 'file']

class UpdateOfferJobUserForm(forms.ModelForm):
    class Meta:
        model = OffersJobUser
        fields = ['is_accept']

class AddOfferJobUserForm(forms.ModelForm):
    user = forms.ModelChoiceField(queryset=User.objects.none(), label="Wyślij zaproszenie do")

    class Meta:
        model = OffersJobUser
        fields = ['user']

class CourseForm(forms.ModelForm):
    category = forms.ModelMultipleChoiceField(
        queryset=CategoryCourse.objects.all(),
        widget=forms.CheckboxSelectMultiple # lub inny widget, np. forms.SelectMultiple
    )
    tags = forms.ModelMultipleChoiceField(
        queryset=TagCourse.objects.all(),
        widget=forms.CheckboxSelectMultiple # lub inny widget, np. forms.SelectMultiple
    )

    class Meta:
        model = Course
        fields = ['title', 'tags', 'category']

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

class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answers
        fields = ['answer']

class PortfolioForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=TagPortfolio.objects.all(),
        widget=forms.CheckboxSelectMultiple # lub inny widget, np. forms.SelectMultiple
    )

    class Meta:
        model = Portfolio
        fields = ['tags', 'title']

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