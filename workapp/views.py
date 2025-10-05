from itertools import chain
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.db import transaction
from django.db.models import Q, Count, Case, When
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView, UpdateView, DeleteView
from django.shortcuts import redirect, render
from django.template.loader import get_template
from django.views import View
import time
import os
import numpy as np
import json
import openai
import fuzz
from django.views.decorators.csrf import csrf_exempt
from typing import List, Dict, Any, Optional
from django.contrib.auth import login
from django.template import TemplateDoesNotExist
import logging
from django.http import HttpResponse, Http404, HttpResponseNotFound
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from .utils import rsa_encrypt
from .models import CV, HR, TagBusiness, TagPortfolio, TagCourse, Test, Portfolio, Projects, Link, Experience, CategoryCourse, CategoryEmploy, Certificate, Course, OffersJob, OffersJobUser, Business, Subject, TestScore, Answers, Questions, Hobby, Skills, Education, Questionnaire
from .forms import CVForm, HRForm, SubjectForm, AddOfferJobUserForm, UpdateOfferJobUserForm, AnswerForm, CourseForm, TestForm, LinkForm, ProjectForm, BusinessForm, QuestionForm, OfferJobsForm, PortfolioForm, ExperienceForm, QuestionFormSet, ExperienceFormSet, LinkFormSet, ProjectsFormSet, SubjectFormSet, QuestionnaireForm, HobbyForm, SkillsForm, EducationForm, EducationFormSet, SkillsFormSet, HobbyFormSet
# Create your views here.

logger = logging.getLogger(__name__)

def check_template(template_name, request):
    try:
        get_template(template_name)
        logger.info(f"Template '{template_name}' found.")
        return True
    except TemplateDoesNotExist:
        logger.error(f"Template '{template_name}' does not exist.")
        return False

class SignUpView(CreateView):
    form_class = UserCreationForm
    template_name = 'signup.html'
    success_url = reverse_lazy('index')

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Template not found.")
        if request.user.is_authenticated:
            messages.info(request, "You are already registered and logged in.")
            return redirect('index')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, "Registration successful. Please log in.")
        return response

class EditProfileView(LoginRequiredMixin, UpdateView):
    form_class = UserChangeForm
    template_name = 'edit_profile.html'
    success_url = reverse_lazy('index')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Profile updated successfully.")
        return response

class DeleteAccountView(LoginRequiredMixin, DeleteView):
    template_name = 'delete_account.html'
    success_url = reverse_lazy('login')

    def get_object(self, queryset=None):
        if self.request.user.is_authenticated:
            return self.request.user
        raise Http404("You are not logged in.")

    def delete(self, request, *args, **kwargs):
        try:
            response = super().delete(request, *args, **kwargs)
            messages.success(request, "Account deleted successfully.")
            return response
        except Exception as e:
            logger.error(f"An error occurred during account deletion: {str(e)}")
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('delete_account')

class CustomLoginView(LoginView):
    template_name = 'login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        if not check_template(self.template_name, self.request):
            return HttpResponse("Template not found.")
        
        remember_me = form.cleaned_data.get('remember_me', False)
        if remember_me:
            self.request.session.set_expiry(1209600)  # 2 weeks in seconds
        messages.success(self.request, "Login successful.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('index')

class CustomLogoutView(LoginRequiredMixin, LogoutView):
    next_page = 'login'

    def dispatch(self, request, *args, **kwargs):
        messages.info(request, "You have been logged out.")
        return super().dispatch(request, *args, **kwargs)
#Rekruter
# === HR ===

class AddHRView(LoginRequiredMixin, CreateView):
    form_class = HRForm
    template_name = 'add_hr.html'

    def form_valid(self, form):
        business_id = self.kwargs.get('business_id')
        business = get_object_or_404(Business, id=business_id)
        form.instance.user = self.request.user

        # save first to get the HR instance with a primary key
        response = super().form_valid(form)

        # now set the many-to-many relation
        form.instance.business.set([business])

        return response

    def get_success_url(self):
        business_id = self.kwargs.get('business_id')
        hr_id = self.object.id
        return reverse('add_offer_jobs', kwargs={'business_id': business_id, 'hr_id': hr_id})

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)
    
class UpdateHRView(LoginRequiredMixin, UpdateView):
    model = HR
    form_class = HRForm
    template_name = 'update_hr.html'

    def get_object(self, queryset=None):
        hr_id = self.kwargs.get('hr_id')
        business_id = self.kwargs.get('business_id')
        return get_object_or_404(HR, id=hr_id, business=business_id, user=self.request.user)

    def get_success_url(self):
        business = self.object.business.first()  # jeśli to ManyToMany
        return reverse('hr_to_business_view', kwargs={'business_id': business.id})

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)


# === Business ===

class AddBusinessView(LoginRequiredMixin, CreateView):
    form_class = BusinessForm
    template_name = 'add_business.html'
    success_url = reverse_lazy('add_hr')

    def get_success_url(self):
        return reverse('add_hr', args=[self.object.id])

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)
    
class UpdateBusinessView(LoginRequiredMixin, UpdateView):
    model = Business
    form_class = BusinessForm
    template_name = 'update_business.html'

    def get_object(self, queryset=None):
        business_id = self.kwargs.get('business_id')
        return get_object_or_404(Business, id=business_id)

    def get_success_url(self):
        return reverse('hr_to_business_view', kwargs={'business_id': self.object.id})

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)


# === OffersJob ===

class AddOfferJobsView(LoginRequiredMixin, CreateView):
    form_class = OfferJobsForm
    template_name = 'add_offer_jobs.html'

    def form_valid(self, form):
        business_id = self.kwargs.get('business_id')
        hr_id = self.kwargs.get('hr_id')

        business = get_object_or_404(Business, id=business_id)
        hr = get_object_or_404(HR, id=hr_id, user=self.request.user)

        form.instance.user = self.request.user
        form.instance.business = business  # assuming ForeignKey or ManyToMany handled in model
        form.instance.hr = hr  # assuming ForeignKey to HR in OfferJobs model

        return super().form_valid(form)

    def get_success_url(self):
        # Redirect wherever you want after creating an OfferJob
        return reverse('offers_job_created_by_user')

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)



class DeleteOffersJobsView(LoginRequiredMixin, DeleteView):
    model = OffersJob
    template_name = 'delete_offer_jobs.html'

    def get_object(self, queryset=None):
        offer_jobs_id = self.kwargs.get('offer_jobs_id')
        return get_object_or_404(OffersJob, id=offer_jobs_id)

    def form_valid(self, form):
        offer = self.get_object()
        if offer.hr.user != self.request.user:
            messages.error(self.request, "Nie masz uprawnień do usunięcia tej oferty.")
            return redirect('offers_job_created_by_user')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('offers_job_created_by_user')

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)


# === OfferJobsUser ===

class AddOfferJobsUserView(LoginRequiredMixin, CreateView):
    form_class = AddOfferJobUserForm
    template_name = 'add_offer_jobs_user.html'

    def form_valid(self, form):
        offers_job_id = self.kwargs.get('offers_job_id')
        offer = get_object_or_404(OffersJob, id=offers_job_id)
        form.instance.user = self.request.user
        form.instance.offer = offer
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('index')

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)


class UpdateOfferJobsUserView(LoginRequiredMixin, UpdateView):
    model = OffersJobUser  # Zakładam, że taki model istnieje
    form_class = UpdateOfferJobUserForm
    template_name = 'update_offer_jobs_user.html'

    def get_object(self, queryset=None):
        offers_job_id = self.kwargs.get('offers_job_id')
        return get_object_or_404(OffersJobUser, offer__id=offers_job_id, user=self.request.user)

    def get_success_url(self):
        return reverse('index')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)
#Rekruter

#Kurs
    
# === COURSE ===

class AddCourseView(LoginRequiredMixin, CreateView):
    form_class = CourseForm
    template_name = 'add_course.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('add_subject', args=[self.object.id])

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)


class UpdateCourseView(LoginRequiredMixin, UpdateView):
    model = Course
    form_class = CourseForm
    template_name = 'update_course.html'

    def get_object(self, queryset=None):
        course_id = self.kwargs.get('course_id')
        return get_object_or_404(Course, id=course_id, author=self.request.user)

    def get_success_url(self):
        return reverse('subject_to_course_view', kwargs={'user_pk': self.request.user.pk})

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)


class DeleteCourseView(LoginRequiredMixin, DeleteView):
    model = Course
    template_name = 'delete_course.html'

    def get_object(self, queryset=None):
        course_id = self.kwargs.get('course_id')
        return get_object_or_404(Course, id=course_id, author=self.request.user)

    def get_success_url(self):
        return reverse('add_course', kwargs={'user_pk': self.request.user.pk})

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)


# === SUBJECT ===

class AddSubjectView(LoginRequiredMixin, CreateView):
    form_class = SubjectFormSet
    template_name = 'add_subject.html'

    def form_valid(self, form):
        form.instance.course_id = self.kwargs['course_id']  # <-- ustawienie relacji z Course
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('add_test', args=[self.kwargs['course_id'], self.object.id])

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)


class UpdateSubjectView(LoginRequiredMixin, UpdateView):
    model = Subject
    form_class = SubjectFormSet
    template_name = 'update_subject.html'

    def get_object(self, queryset=None):
        course_id = self.kwargs.get('course_id')
        subject_id = self.kwargs.get('subject_id')
        return get_object_or_404(Subject, id=subject_id, course=course_id, user=self.request.user)

    def get_success_url(self):
        return reverse('subject_to_test_view', kwargs={'user_pk': self.request.user.pk})

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)


class DeleteSubjectView(LoginRequiredMixin, DeleteView):
    model = Subject
    template_name = 'delete_subject.html'

    def get_object(self, queryset=None):
        course_id = self.kwargs.get('course_id')
        subject_id = self.kwargs.get('subject_id')
        return get_object_or_404(Subject, id=subject_id, course=course_id, user=self.request.user)

    def get_success_url(self):
        return reverse('add_subject', kwargs={'user_pk': self.request.user.pk})

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)


# === TEST ===

class AddTestView(LoginRequiredMixin, CreateView):
    form_class = TestForm
    template_name = 'add_test.html'

    def form_valid(self, form):
        form.instance.subject_id = self.kwargs['subject_id']  # <-- ustawienie relacji z Subject
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('add_question', args=[
            self.kwargs['course_id'],
            self.kwargs['subject_id'],
            self.object.id
        ])

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)


class UpdateTestView(LoginRequiredMixin, UpdateView):
    model = Test
    form_class = TestForm
    template_name = 'update_test.html'

    def get_object(self, queryset=None):
        subject_id = self.kwargs.get('subject_id')
        test_id = self.kwargs.get('test_id')
        return get_object_or_404(Test, id=test_id, subject=subject_id)

    def get_success_url(self):
        return reverse('test_to_question_view')

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)


class DeleteTestView(LoginRequiredMixin, DeleteView):
    model = Test
    template_name = 'delete_test.html'

    def get_object(self, queryset=None):
        subject_id = self.kwargs.get('subject_id')
        test_id = self.kwargs.get('test_id')
        return get_object_or_404(Test, id=test_id, subject=subject_id)

    def get_success_url(self):
        return reverse('add_test')

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)


# === QUESTIONS ===

class AddQuestionView(LoginRequiredMixin, View):
    template_name = 'add_questions.html'
    
    def get(self, request, *args, **kwargs):
        formset = QuestionFormSet(queryset=Questions.objects.none())
        return render(request, self.template_name, {'formset': formset})
    
    def post(self, request, *args, **kwargs):
        formset = QuestionFormSet(request.POST)
        if formset.is_valid():
            test_id = self.kwargs['test_id']
            for instance in formset.save(commit=False):
                instance.test_id = test_id
                instance.save()
            return redirect(reverse('course_user'))
        return render(request, self.template_name, {'formset': formset})


class UpdateQuestionView(LoginRequiredMixin, UpdateView):
    model = Questions
    form_class = QuestionForm
    template_name = 'update_question.html'

    def get_object(self, queryset=None):
        test_id = self.kwargs.get('test_id')
        question_id = self.kwargs.get('question_id')
        return get_object_or_404(Questions, id=question_id, test=test_id)

    def get_success_url(self):
        return reverse('test_to_question_view')

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)


class DeleteQuestionView(LoginRequiredMixin, DeleteView):
    model = Questions
    template_name = 'delete_question.html'

    def get_object(self, queryset=None):
        test_id = self.kwargs.get('test_id')
        question_id = self.kwargs.get('question_id')
        return get_object_or_404(Questions, id=question_id, test=test_id)

    def get_success_url(self):
        return reverse('add_question')

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)


# === ANSWERS ===

class AddAnswersView(LoginRequiredMixin, CreateView):
    form_class = AnswerForm
    template_name = 'add_answers.html'
    success_url = reverse_lazy('search_stores')  # fallback

    def get_question(self):
        question_id = self.kwargs.get('question_id')
        return get_object_or_404(Questions, id=question_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['question'] = self.get_question()
        return context

    @transaction.atomic
    def form_valid(self, form):
        form.instance.user = self.request.user
        question = self.get_question()
        test = question.test

        answer_text = form.cleaned_data.get('answer').strip().lower()
        correct_answer = question.correct.strip().lower()

        test_score, _ = TestScore.objects.get_or_create(
            user=self.request.user,
            test=test,
            defaults={'score': 0, 'minimum': 0}
        )

        if correct_answer in answer_text:
            test_score.score += 1
            test_score.save()

        form.instance.question = question
        form.save()

        # Pobierz kolejne pytanie
        next_question = Questions.objects.filter(
            test=test,
            id__gt=question.id
        ).order_by('id').first()

        if next_question:
            return redirect('answer_question',
                            course_id=test.subject.course.id,
                            subject_id=test.subject.id,
                            test_id=test.id,
                            question_id=next_question.id)
        else:
            return redirect('search_stores', subject_id=test.subject.id)

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)
    
class AddQuestionnaireView(LoginRequiredMixin, CreateView):
    form_class = QuestionnaireForm
    template_name = 'questionnaire.html'

    def form_valid(self, form):
        hr_id = self.kwargs.get('subject_id')

        hr = get_object_or_404(Subject, id=hr_id)

        form.instance.subject = hr  # assuming ForeignKey to HR in OfferJobs model

        return super().form_valid(form)

    def get_success_url(self):
        # Redirect wherever you want after creating an OfferJob
        return reverse('thanks')

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)
                  
#Kurs

#Portfolio

class AddPortfolioView(LoginRequiredMixin, CreateView):
    form_class = PortfolioForm
    template_name = 'add_portfolio.html'
    success_url = reverse_lazy('portfolio_to_user_view')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)


class UpdatePortfolioView(LoginRequiredMixin, UpdateView):
    model = Portfolio
    form_class = PortfolioForm
    template_name = 'update_portfolio.html'

    def get_object(self, queryset=None):
        portfolio_id = self.kwargs.get('portfolio_id')
        return get_object_or_404(Portfolio, id=portfolio_id, user=self.request.user)

    def get_success_url(self):
        return reverse('portfolio_to_user_view')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)


# === Project ===

class AddProjectView(LoginRequiredMixin, CreateView):
    template_name = 'add_project.html'
    
    def get(self, request, *args, **kwargs):
        formset = ProjectsFormSet(queryset=Projects.objects.none())
        return render(request, self.template_name, {'formset': formset})
    
    def post(self, request, *args, **kwargs):
        formset = ProjectsFormSet(request.POST, request.FILES)
        if formset.is_valid():
            portfolio_id = self.kwargs['portfolio_id']
            for instance in formset.save(commit=False):
                instance.portfolio_id = portfolio_id
                instance.save()
            return redirect(reverse('my_portfolio_projects_view'))
        return render(request, self.template_name, {'formset': formset})


class UpdateProjectView(LoginRequiredMixin, UpdateView):
    model = Projects
    form_class = ProjectForm
    template_name = 'update_project.html'

    def get_object(self, queryset=None):
        portfolio_id = self.kwargs.get('portfolio_id')
        project_id = self.kwargs.get('project_id')
        return get_object_or_404(Projects, id=project_id, portfolio=portfolio_id, portfolio__user=self.request.user)

    def get_success_url(self):
        return reverse('my_portfolio_projects_view')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)


# === Link ===

class AddLinkView(LoginRequiredMixin, CreateView):
    template_name = 'add_link.html'
    
    def get(self, request, *args, **kwargs):
        formset = LinkFormSet(queryset=Link.objects.none())
        return render(request, self.template_name, {'formset': formset})
    
    def post(self, request, *args, **kwargs):
        formset = LinkFormSet(request.POST)
        if formset.is_valid():
            portfolio_id = self.kwargs['portfolio_id']
            for instance in formset.save(commit=False):
                instance.portfolio_id = portfolio_id
                instance.save()
            return redirect(reverse('my_portfolio_links_view'))
        return render(request, self.template_name, {'formset': formset})


class UpdateLinkView(LoginRequiredMixin, UpdateView):
    model = Link
    form_class = LinkForm
    template_name = 'update_link.html'

    def get_object(self, queryset=None):
        portfolio_id = self.kwargs.get('portfolio_id')
        link_id = self.kwargs.get('link_id')
        return get_object_or_404(Link, id=link_id, portfolio=portfolio_id, portfolio__user=self.request.user)

    def get_success_url(self):
        return reverse('my_portfolio_links_view')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)
#Portfolio

# === CV ===

class AddCVView(LoginRequiredMixin, CreateView):
    form_class = CVForm
    template_name = 'add_cv.html'
    success_url = reverse_lazy('add_experience')

    def get_success_url(self):
        return reverse('add_experience', args=[self.object.id])

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)


class UpdateCVView(LoginRequiredMixin, UpdateView):
    model = CV
    form_class = CVForm
    template_name = 'update_cv.html'

    def get_object(self, queryset=None):
        cv_id = self.kwargs.get('cv_id')
        return get_object_or_404(CV, id=cv_id, user=self.request.user)

    def get_success_url(self):
        return reverse('cv_to_user_view')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)


# === EXPERIENCE ===

class AddExperienceView(LoginRequiredMixin, CreateView):
    template_name = 'add_experience.html'

    def get(self, request, *args, **kwargs):
        formset = ExperienceFormSet(queryset=Experience.objects.none())
        return render(request, self.template_name, {'formset': formset})
    
    def post(self, request, *args, **kwargs):
        formset = ExperienceFormSet(request.POST)
        if formset.is_valid():
            cv_id = self.kwargs['cv_id']
            for instance in formset.save(commit=False):
                instance.cv_id = cv_id
                instance.save()
            return redirect(reverse('my_cv_experience_view'))
        return render(request, self.template_name, {'formset': formset})


class UpdateExperienceView(LoginRequiredMixin, UpdateView):
    model = Experience
    form_class = ExperienceForm
    template_name = 'update_experience.html'

    def get_object(self, queryset=None):
        cv_id = self.kwargs.get('cv_id')
        experience_id = self.kwargs.get('experience_id')
        return get_object_or_404(Experience, id=experience_id, cv=cv_id, cv__user=self.request.user)

    def get_success_url(self):
        return reverse('my_cv_experience_view')

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)
    
class AddHobbyView(LoginRequiredMixin, CreateView):
    template_name = 'add_hobby.html'

    def get(self, request, *args, **kwargs):
        formset = HobbyFormSet(queryset=Hobby.objects.none())
        return render(request, self.template_name, {'formset': formset})
    
    def post(self, request, *args, **kwargs):
        formset = HobbyFormSet(request.POST)
        if formset.is_valid():
            cv_id = self.kwargs['cv_id']
            for instance in formset.save(commit=False):
                instance.cv_id = cv_id
                instance.save()
            return redirect(reverse('my_cv_hobby_view'))
        return render(request, self.template_name, {'formset': formset})
    
class UpdateHobbyView(LoginRequiredMixin, UpdateView):
    model = Hobby
    form_class = HobbyForm
    template_name = 'update_hobby.html'

    def get_object(self, queryset=None):
        cv_id = self.kwargs.get('cv_id')
        experience_id = self.kwargs.get('hobby_id')
        return get_object_or_404(Hobby, id=experience_id, cv=cv_id, cv__user=self.request.user)

    def get_success_url(self):
        return reverse('my_cv_hobby_view')

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)
    
class AddSkillsView(LoginRequiredMixin, CreateView):
    template_name = 'add_skills.html'

    def get(self, request, *args, **kwargs):
        formset = SkillsFormSet(queryset=Skills.objects.none())
        return render(request, self.template_name, {'formset': formset})
    
    def post(self, request, *args, **kwargs):
        formset = SkillsFormSet(request.POST)
        if formset.is_valid():
            cv_id = self.kwargs['cv_id']
            for instance in formset.save(commit=False):
                instance.cv_id = cv_id
                instance.save()
            return redirect(reverse('my_cv_skills_view'))
        return render(request, self.template_name, {'formset': formset})
    
class UpdateSkillsView(LoginRequiredMixin, UpdateView):
    model = Skills
    form_class = SkillsForm
    template_name = 'update_skills.html'

    def get_object(self, queryset=None):
        cv_id = self.kwargs.get('cv_id')
        experience_id = self.kwargs.get('skill_id')
        return get_object_or_404(Skills, id=experience_id, cv=cv_id, cv__user=self.request.user)

    def get_success_url(self):
        return reverse('my_cv_skills_view')

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)
    
class AddEducationView(LoginRequiredMixin, CreateView):
    template_name = 'add_education.html'

    def get(self, request, *args, **kwargs):
        formset = EducationFormSet(queryset=Education.objects.none())
        return render(request, self.template_name, {'formset': formset})
    
    def post(self, request, *args, **kwargs):
        formset = EducationFormSet(request.POST)
        if formset.is_valid():
            cv_id = self.kwargs['cv_id']
            for instance in formset.save(commit=False):
                instance.cv_id = cv_id
                instance.save()
            return redirect(reverse('my_cv_education_view'))
        return render(request, self.template_name, {'formset': formset})
    
class UpdateEducationView(LoginRequiredMixin, UpdateView):
    model = Education
    form_class = EducationForm
    template_name = 'update_education.html'

    def get_object(self, queryset=None):
        cv_id = self.kwargs.get('cv_id')
        experience_id = self.kwargs.get('education_id')
        return get_object_or_404(Education, id=experience_id, cv=cv_id, cv__user=self.request.user)

    def get_success_url(self):
        return reverse('my_cv_education_view')

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)
    
@transaction.atomic
@login_required
def search_business(request):
    template_name = 'search_business.html'

    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")

    query = request.GET.get('q', '').strip()
    businesses = []
    tags = []

    try:
        if query:
            businesses = Business.objects.filter(Q(name__icontains=query))
            tags = TagBusiness.objects.filter(Q(name__icontains=query))
        else:
            businesses = Business.objects.all()

        logger.info(f"Business and tags retrieved successfully for user {request.user}. Query: '{query}'")
    except Exception as e:
        logger.error(f"Error retrieving businesses or tags for user {request.user}: {e}")
        return HttpResponse("An error occurred while retrieving data.", status=500)

    # Można też połączyć wyniki (jeśli chcesz wyświetlać jako jedna lista)
    products = list(chain(businesses, tags))

    return render(request, template_name, {
        'products': products,
        'query': query
    })

@transaction.atomic
@login_required
def search_offers_job(request):
    template_name = 'search_offers_job.html'

    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")

    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category')
    categories = CategoryEmploy.objects.all()
    products = []

    try:
        offers_query = OffersJob.objects.all()

        if query:
            offers_query = offers_query.filter(Q(title__icontains=query))

        if category_id:
            offers_query = offers_query.filter(category_id=category_id)

        products = offers_query

        logger.info(
            f"Offers retrieved successfully for user {request.user}. "
            f"Query: '{query}', Category: '{category_id}'"
        )
    except Exception as e:
        logger.error(f"Error retrieving offers for user {request.user}: {e}")
        return HttpResponse("An error occurred while retrieving offers.", status=500)

    return render(request, template_name, {
        'products': products,
        'query': query,
        'categories': categories,
        'selected_category': category_id
    })

@transaction.atomic
def accepted_offers_job_user(request):
    template_name = 'accepted_offers_job_user.html'
    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")

    try:
        user = request.user
        products = OffersJobUser.objects.filter(is_accept=True, user=user)
        logger.info(f"Products retrieved successfully for user {request.user}.")
    except Exception as e:
        logger.error(f"Error retrieving categories for user {request.user}: {e}")
        products = []
        return HttpResponse("An error occurred while retrieving categories.", status=500)
    
    return render(request, template_name, {'products': products})

@transaction.atomic
def offer_jobs_id(request, business_id, hr_id):
    template_name = 'offer_jobs_id.html'
    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")

    try:
        products = OffersJob.objects.filter(business=business_id, hr=hr_id)
    except Exception as e:
        products = []
        return HttpResponse("An error occurred while retrieving categories.", status=500)
    
    return render(request, template_name, {'products': products})

@transaction.atomic
def offer_jobs_id_one(request, business_id, hr_id, offer_id):
    template_name = 'offer_jobs_id_one.html'
    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")

    try:
        products = get_object_or_404(OffersJob, business=business_id, hr=hr_id, id=offer_id)
    except Exception as e:
        logger.error(f"Error retrieving offer: {e}")
        return HttpResponse("An error occurred while retrieving the offer.", status=500)

    return render(request, template_name, {'products': products})

#new view
@transaction.atomic
def offer_user_to_hr(request, offer_id):
    template_name = 'offer_user_to_hr.html'

    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")

    try:
        # Get the Offer instance
        offer = get_object_or_404(OffersJob, id=offer_id)
        
        # Get the HR user related to the offer
        hr_user = offer.hr.user
        
        # Create the OffersJobUser entry
        products = OffersJobUser.objects.create(offer=offer, user=hr_user)

        # Success message
        message = "Udało się aplikować na ofertę pracy"
    except Exception as e:
        logger.error(f"Error creating OffersJobUser: {e}")
        return HttpResponse("An error occurred while processing the offer.", status=500)

    return render(request, template_name, {'products': products, 'message': message})

@transaction.atomic
def offers_job_user(request):
    template_name = 'offers_job_user.html'
    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")

    try:
        user = request.user
        products = OffersJobUser.objects.filter(user=user)
        logger.info(f"Products retrieved successfully for user {request.user}.")
    except Exception as e:
        logger.error(f"Error retrieving categories for user {request.user}: {e}")
        products = []
        return HttpResponse("An error occurred while retrieving categories.", status=500)
    
    return render(request, template_name, {'products': products})

@transaction.atomic
def offers_job_created_by_user(request):
    template_name = 'offers_job_created_by_user.html'
    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")

    try:
        user = request.user
        products = OffersJob.objects.filter(hr__user=user)
        logger.info(f"Products retrieved successfully for user {request.user}.")
    except Exception as e:
        logger.error(f"Error retrieving categories for user {request.user}: {e}")
        products = []
        return HttpResponse("An error occurred while retrieving categories.", status=500)
    
    return render(request, template_name, {'products': products})

@transaction.atomic
def hr_to_business_view(request):
    template_name = 'hr_business_list.html'

    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")

    try:
        hr = HR.objects.get(user=request.user)
        products = hr.business.all()
        logger.info(f"Businesses retrieved successfully for HR {hr}.")
    except HR.DoesNotExist:
        logger.warning(f"HR profile not found for user {request.user}.")
        return HttpResponse("No HR profile found for this user.", status=404)
    except Exception as e:
        logger.exception(f"Unexpected error while retrieving businesses for user {request.user}: {e}")
        return HttpResponse("An error occurred while retrieving businesses.", status=500)

    return render(request, template_name, {'products': products})

@transaction.atomic
@login_required
def search_course_view(request):
    template_name = 'search_course.html'

    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")

    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category')
    categories = CategoryCourse.objects.all()
    courses = []
    tags = []

    try:
        course_query = Course.objects.all()

        if query:
            course_query = course_query.filter(Q(title__icontains=query))
            tags = TagCourse.objects.filter(Q(name__icontains=query))
        else:
            tags = TagCourse.objects.none()  # lub wszystkie, jeśli chcesz: TagCourse.objects.all()

        if category_id:
            course_query = course_query.filter(category_id=category_id)

        courses = course_query

        logger.info(
            f"Courses and tags retrieved successfully for user {request.user}. "
            f"Query: '{query}', Category: '{category_id}'"
        )
    except Exception as e:
        logger.error(f"Error retrieving courses or tags for user {request.user}: {e}")
        return HttpResponse("An error occurred while retrieving data.", status=500)

    return render(
        request,
        template_name,
        {
            'courses': courses,
            'tags': tags,
            'query': query,
            'categories': categories,
            'selected_category': category_id
        }
    )

@login_required
@transaction.atomic
def subject_to_course_view(request, course_id):
    template_name = 'subject_list.html'

    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")

    try:
        course = get_object_or_404(Course, id=course_id)
        products = Subject.objects.filter(course=course)
        logger.info(f"Subjects retrieved successfully for Course {course.title} by user {request.user}.")
    except Exception as e:
        logger.exception(f"Error retrieving subjects for course {course_id} by user {request.user}: {e}")
        return HttpResponse("An error occurred while retrieving subjects.", status=500)

    return render(request, template_name, {'course': course,'products': products})

@login_required
@transaction.atomic
def course_to_certificate_view(request):
    template_name = 'course_certificate_list.html'

    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")

    try:
        user = request.user
        products = Certificate.objects.filter(user=user)
        logger.info(f"Certificates retrieved successfully for user {request.user}.")
    except Exception as e:
        logger.error(f"Error retrieving certificates for user {request.user}: {e}")
        return HttpResponse("An error occurred while retrieving certificates.", status=500)

    return render(request, template_name, {'products': products})

@transaction.atomic
def subject_to_test_view(request, subject_id, course_id):
    template_name = 'test_list.html'
    
    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")

    try:
        subject = get_object_or_404(Subject, id=subject_id, course__id=course_id)
        products = Test.objects.filter(subject=subject)
        logger.info(f"Tests for course {subject.title} retrieved successfully by user {request.user}.")
    except Exception as e:
        logger.error(f"Error retrieving tests for course {subject_id}: {e}")
        return HttpResponse("An error occurred while retrieving tests.", status=500)

    return render(request, template_name, {'products': products})

@transaction.atomic
def test_to_question_view(request, test_id):
    template_name = 'questions_list.html'

    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")

    try:
        test = get_object_or_404(Test, id=test_id)
        products = Questions.objects.filter(test=test)
        logger.info(f"Questions for test '{test.title}' retrieved successfully by user {request.user}.")
    except Exception as e:
        logger.error(f"Error retrieving questions for test ID {test_id}: {e}")
        return HttpResponse("An error occurred while retrieving questions.", status=500)

    return render(request, template_name, {'products': products})

@transaction.atomic
@login_required
def search_stores(request, subject_id):
    template_name = 'course_cert_generate.html'

    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")

    try:
        subject = get_object_or_404(Subject, id=subject_id)
        course = subject.course
        tests = Test.objects.filter(subject=subject)
        test_score = TestScore.objects.filter(user=request.user, test__in=tests).order_by('-id').first()

        products = []

        if test_score and test_score.score > test_score.minimum:
            if tests.filter(is_finish=True).exists():
                # Zapobieganie duplikatom certyfikatów
                certificate, created = Certificate.objects.get_or_create(
                    user=request.user,
                    course=course,
                    defaults={'name': f"Certificate for {course.title}"}
                )
                if created:
                    logger.info(f"Certificate created successfully for user {request.user}.")
                else:
                    logger.info(f"Certificate already exists for user {request.user}.")
                products = [certificate]

    except Exception as e:
        logger.error(f"Error processing certificate for user {request.user}: {e}")
        return HttpResponse("An error occurred while processing your request.", status=500)

    return render(request, template_name, {'products': products, 'test_score': test_score})

@transaction.atomic
def test_score_to_user_view(request):
    template_name = 'test_score_list.html'
    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")

    try:
        products = TestScore.objects.filter(user=request.user)
        logger.info(f"Products retrieved successfully for user {request.user}.")
    except Exception as e:
        logger.error(f"Error retrieving categories for user {request.user}: {e}")
        products = []
        return HttpResponse("An error occurred while retrieving categories.", status=500)
    
    return render(request, template_name, {'products': products})

@transaction.atomic
@login_required
def search_portfolio(request):
    template_name = 'search_portfolio.html'

    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")

    query = request.GET.get('q', '').strip()
    portfolios = []
    tags = []

    try:
        if query:
            portfolios = Portfolio.objects.filter(Q(title__icontains=query))
            tags = TagPortfolio.objects.filter(Q(name__icontains=query))
        else:
            portfolios = Portfolio.objects.all()

        logger.info(f"Search executed by {request.user}: query='{query}'")
    except Exception as e:
        logger.error(f"Error during search for user {request.user}: {e}")
        return HttpResponse("An error occurred during the search.", status=500)

    return render(request, template_name, {
        'portfolios': portfolios,
        'tags': tags,
        'query': query
    })

@transaction.atomic
@login_required
def search_cv(request):
    """
    Wyszukiwanie CV po tytule (query 'q') i zwracanie JSON.
    """
    query = request.GET.get('q', '').strip()

    try:
        if query:
            cvs = CV.objects.filter(title__icontains=query)
        else:
            cvs = CV.objects.all()

        cv_user = CV.objects.filter(user=request.user)
        hr_user = HR.objects.filter(user=request.user)

        cvs_data = []
        for cv in cvs:
            if not cv_user.exists() and not hr_user.exists():
                number_phone = rsa_encrypt(cv.number_phone)
                street = rsa_encrypt(cv.street)
                number_house = rsa_encrypt(cv.number_house)
                code = rsa_encrypt(cv.code)
                city = rsa_encrypt(cv.city)
            else:
                number_phone = cv.number_phone
                street = cv.street
                number_house = cv.number_house
                code = cv.code
                city = cv.city

            cvs_data.append({
                "id": cv.id,
                "title": cv.title,
                "first_name": cv.first_name,
                "last_name": cv.last_name,
                "email": cv.email,
                "number_phone": number_phone,
                "street": street,
                "number_house": number_house,
                "code": code,
                "city": city,
                "user_id": cv.user.id
            })

        # render do szablonu
        return render(request, "search_cv.html", {
            "query": query,
            "cvs": cvs_data
        })

    except Exception as e:
        return render(request, "search_cv.html", {
            "query": query,
            "error": f"An error occurred during CV search: {str(e)}"
        })


@transaction.atomic
def portfolio_to_user_view(request):
    template_name = 'portfolio_user_list.html'
    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")

    try:
        products = Portfolio.objects.filter(user=request.user)
        logger.info(f"Products retrieved successfully for user {request.user}.")
    except Exception as e:
        logger.error(f"Error retrieving categories for user {request.user}: {e}")
        products = []
        return HttpResponse("An error occurred while retrieving categories.", status=500)
    
    return render(request, template_name, {'products': products})

@transaction.atomic
def cv_to_id_view(request, cv_id):
    template_name = 'cv_id_list.html'
    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")

    try:
        products = get_object_or_404(CV, id=cv_id)
        logger.info(f"Products retrieved successfully for user {request.user}.")
    except Exception as e:
        logger.error(f"Error retrieving categories for user {request.user}: {e}")
        products = []
        return HttpResponse("An error occurred while retrieving categories.", status=500)
    
    return render(request, template_name, {'products': products})

@transaction.atomic
def thanking_view(request):
    template_name = 'thanks.html'
    return render(request, template_name)

@transaction.atomic
def cv_to_user_view(request):
    template_name = 'cv_user_list.html'
    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")

    try:
        products = CV.objects.filter(user=request.user)
        logger.info(f"Products retrieved successfully for user {request.user}.")
    except Exception as e:
        logger.error(f"Error retrieving categories for user {request.user}: {e}")
        products = []
        return HttpResponse("An error occurred while retrieving categories.", status=500)
    
    return render(request, template_name, {'products': products})

@transaction.atomic
def course_user(request):
    template_name = 'course_user.html'
    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")

    try:
        products = Course.objects.filter(author=request.user)
        logger.info(f"Products retrieved successfully for user {request.user}.")
    except Exception as e:
        logger.error(f"Error retrieving categories for user {request.user}: {e}")
        products = []
        return HttpResponse("An error occurred while retrieving categories.", status=500)
    
    return render(request, template_name, {'products': products})

@transaction.atomic
def my_cv_hobby_view(request):
    template_name = 'my_hobby_list.html'
    
    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")
    
    try:
        cv = get_object_or_404(CV, user=request.user)
        experiences = Hobby.objects.filter(cv=cv)
        logger.info(f"Experiences for CV '{cv.title}' retrieved successfully by user {request.user}.")
    except Exception as e:
        logger.error(f"Error retrieving experiences for user {request.user}: {e}")
        return HttpResponse("An error occurred while retrieving experiences.", status=500)
    
    return render(request, template_name, {'products': experiences, 'cv_id': cv.id})

@transaction.atomic
def cv_hobby_view(request, cv_id):
    template_name = 'hobby_list.html'
    
    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")
    
    try:
        cv = get_object_or_404(CV, id=cv_id)
        experiences = Hobby.objects.filter(cv=cv)
        logger.info(f"Experiences for CV '{cv.title}' retrieved successfully by user {request.user}.")
    except Exception as e:
        logger.error(f"Error retrieving experiences for user {request.user}: {e}")
        return HttpResponse("An error occurred while retrieving experiences.", status=500)
    
    return render(request, template_name, {'products': experiences})

@transaction.atomic
def my_cv_education_view(request):
    template_name = 'my_education_list.html'
    
    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")
    
    try:
        cv = get_object_or_404(CV, user=request.user)
        experiences = Education.objects.filter(cv=cv)
        logger.info(f"Experiences for CV '{cv.title}' retrieved successfully by user {request.user}.")
    except Exception as e:
        logger.error(f"Error retrieving experiences for user {request.user}: {e}")
        return HttpResponse("An error occurred while retrieving experiences.", status=500)
    
    return render(request, template_name, {'products': experiences, 'cv_id': cv.id})

@transaction.atomic
def cv_education_view(request, cv_id):
    template_name = 'education_list.html'
    
    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")
    
    try:
        cv = get_object_or_404(CV, id=cv_id)
        experiences = Education.objects.filter(cv=cv)
        logger.info(f"Experiences for CV '{cv.title}' retrieved successfully by user {request.user}.")
    except Exception as e:
        logger.error(f"Error retrieving experiences for user {request.user}: {e}")
        return HttpResponse("An error occurred while retrieving experiences.", status=500)
    
    return render(request, template_name, {'products': experiences})

@transaction.atomic
def my_cv_skills_view(request):
    template_name = 'my_skills_list.html'
    
    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")
    
    try:
        cv = get_object_or_404(CV, user=request.user)
        experiences = Skills.objects.filter(cv=cv)
        logger.info(f"Experiences for CV '{cv.title}' retrieved successfully by user {request.user}.")
    except Exception as e:
        logger.error(f"Error retrieving experiences for user {request.user}: {e}")
        return HttpResponse("An error occurred while retrieving experiences.", status=500)
    
    return render(request, template_name, {'products': experiences, 'cv_id': cv.id})

@transaction.atomic
def cv_skills_view(request, cv_id):
    template_name = 'skills_list.html'
    
    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")
    
    try:
        cv = get_object_or_404(CV, id=cv_id)
        experiences = Skills.objects.filter(cv=cv)
        logger.info(f"Experiences for CV '{cv.title}' retrieved successfully by user {request.user}.")
    except Exception as e:
        logger.error(f"Error retrieving experiences for user {request.user}: {e}")
        return HttpResponse("An error occurred while retrieving experiences.", status=500)
    
    return render(request, template_name, {'products': experiences})

@transaction.atomic
def subject_questionnaire_view(request, course_id, subject_id):
    template_name = 'questionnaire_list.html'
    
    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")
    
    try:
        course = get_object_or_404(Course, id=course_id)
        subject = get_object_or_404(Subject, course__id=course.id, id=subject_id)
        experiences = Questionnaire.objects.filter(subject=subject).aggregate(
            yes_count=Count(Case(When(category="tak", then=1))),
            no_count=Count(Case(When(cate="nie", then=1)))
        )
        logger.info(f"Experiences for CV '{subject.title}' retrieved successfully by user {request.user}.")
    except Exception as e:
        logger.error(f"Error retrieving experiences for user {request.user}: {e}")
        return HttpResponse("An error occurred while retrieving experiences.", status=500)
    
    return render(request, template_name, {'products': experiences})

@transaction.atomic
def my_cv_experience_view(request):
    template_name = 'experience_list.html'
    
    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")
    
    try:
        cv = get_object_or_404(CV, user=request.user)
        experiences = Experience.objects.filter(cv=cv)
        logger.info(f"Experiences for CV '{cv.title}' retrieved successfully by user {request.user}.")
    except Exception as e:
        logger.error(f"Error retrieving experiences for user {request.user}: {e}")
        return HttpResponse("An error occurred while retrieving experiences.", status=500)
    
    return render(request, template_name, {'products': experiences, 'cv_id': cv.id})

@transaction.atomic
def cv_id_view(request, cv_id):
    template_name = 'project_list.html'
    
    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")
    
    try:
        cv = get_object_or_404(CV, id=cv_id)
        experiences = Experience.objects.filter(cv=cv)
        logger.info(f"Experiences for CV '{cv.title}' retrieved successfully by user {request.user}.")
    except Exception as e:
        logger.error(f"Error retrieving experiences for user {request.user}: {e}")
        return HttpResponse("An error occurred while retrieving experiences.", status=500)
    
    return render(request, template_name, {'products': experiences})

@transaction.atomic
def portfolio_projects_view(request, portfolio_id):
    template_name = 'portfolio_projects.html'
    
    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")
    
    try:
        portfolio = get_object_or_404(Portfolio, id=portfolio_id)
        projects = Projects.objects.filter(portfolio=portfolio)
        logger.info(f"Projects retrieved successfully for portfolio {portfolio_id} by user {request.user}.")
    except Exception as e:
        logger.error(f"Error retrieving projects for portfolio {portfolio_id} by user {request.user}: {e}")
        return HttpResponse("An error occurred while retrieving projects.", status=500)
    
    return render(request, template_name, {'products': projects})

@transaction.atomic
def my_portfolio_projects_view(request):
    template_name = 'my_portfolio_projects_list.html'
    
    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")
    
    try:
        portfolio = get_object_or_404(Portfolio, user=request.user)
        projects = Projects.objects.filter(portfolio=portfolio)
        logger.info(f"Projects retrieved successfully for user {request.user}.")
    except Exception as e:
        logger.error(f"Error retrieving projects for user {request.user}: {e}")
        return HttpResponse("An error occurred while retrieving projects.", status=500)
    
    return render(request, template_name, {'products': projects})

@transaction.atomic
def my_portfolio_links_view(request):
    template_name = 'my_portfolio_links_list.html'
    
    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")
    
    try:
        portfolio = get_object_or_404(Portfolio, user=request.user)
        links = Link.objects.filter(portfolio=portfolio)
        logger.info(f"Links retrieved successfully for user {request.user}.")
    except Exception as e:
        logger.error(f"Error retrieving links for user {request.user}: {e}")
        return HttpResponse("An error occurred while retrieving links.", status=500)
    
    return render(request, template_name, {'products': links})

#new view
@transaction.atomic
def answer_request_user_view(request):
    template_name = 'answer_question_user.html'
    
    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")
    
    try:
        user = request.user
        answer = Answers.objects.filter(user=user)
        logger.info(f"Links retrieved successfully for user {request.user}.")
    except Exception as e:
        logger.error(f"Error retrieving links for user {request.user}: {e}")
        return HttpResponse("An error occurred while retrieving links.", status=500)
    
    return render(request, template_name, {'answer': answer})

@transaction.atomic
def portfolio_links_view(request, portfolio_id):
    template_name = 'portfolio_links.html'
    
    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")
    
    try:
        portfolio = get_object_or_404(Portfolio, id=portfolio_id)
        links = Link.objects.filter(portfolio=portfolio)
        logger.info(f"Links retrieved successfully for portfolio {portfolio_id} by user {request.user}.")
    except Exception as e:
        logger.error(f"Error retrieving links for portfolio {portfolio_id} by user {request.user}: {e}")
        return HttpResponse("An error occurred while retrieving links.", status=500)
    
    return render(request, template_name, {'products': links})

# Po utworzeniu konta uruchomienie algorytmu AI

def adapt_questions_fuzzy(questions: List[Dict[str, Any]], trait_scores: Dict[str, float]) -> List[Dict[str, Any]]:
    """Dostosowuje poziom trudności pytań do wykrytych predyspozycji.
    Jeśli użytkownik silnie wykazuje pewną predyspozycję, zwiększamy trudność pytań z tej kategorii.
    Używamy prostego progu lub skali rozmytej (jeśli dostępne).
    """
    if not SKFUZZY_AVAILABLE:
    # Zastosowanie poniższego algorytmu w OpenAI
    # Zamiana algorytmu na, wyświetlenie listy kursów po znalezionej kategorii, w którym najwiecej jest odpowiedzi tak, jeśli chodzi o test predyspozycji
    # Jeżeli w dwóch kategoriach jest exekwo odpowiedzi na tak, to przejście do algorytmu, gdzie najwięcej jest ofert pracy
    # Integracja systemów rozmytych (łącznie z Automatami i Językami Formalnymi) z inteligencją obliczeniową
    # Dodanie do tego algorytmów tłumaczeniowych
    # Rozważanie czy zastosować uczenie maszynowe czy systemy dialogowe
        out = []
        for q in questions:
            base = q.get("difficulty", "średni")
            pred = q.get("predisposition", None)
            score = trait_scores.get(pred, 0.5) if pred else 0.5
        if score > 0.7:
            q["difficulty"] = "trudny"
        elif score < 0.3:
            q["difficulty"] = "łatwy"
        else:
            q["difficulty"] = "średni"
            out.append(q)
        return out


    # użycie skfuzzy: zdefiniuj zestaw rozmyty difficulty ~ score
    x = np.arange(0, 1.01, 0.01)
    low = fuzz.trimf(x, [0.0, 0.0, 0.5])
    med = fuzz.trimf(x, [0.0, 0.5, 1.0])
    high = fuzz.trimf(x, [0.5, 1.0, 1.0])


    out = []
    for q in questions:
        pred = q.get("predisposition")
        score = trait_scores.get(pred, 0.5)
        # fuzzify
        low_m = fuzz.interp_membership(x, low, score)
        med_m = fuzz.interp_membership(x, med, score)
        high_m = fuzz.interp_membership(x, high, score)
        # dekodowanie: najwyższe przynależność
        if high_m >= med_m and high_m >= low_m:
            q["difficulty"] = "trudny"
        elif low_m >= med_m and low_m >= high_m:
            q["difficulty"] = "łatwy"
        else:
            q["difficulty"] = "średni"
        out.append(q)
    return out

#Plan aktualizacji aplikacji:
# 1. Opracowanie front-endu
# 2. Dodawanie kryptografii do aplikacji
# 3. Dodawanie algorytmów AI

openai.api_key = os.getenv("OPENAI_API_KEY")


# ============================================================
# Pomocnik: próba wydobycia JSON-a z odpowiedzi LLM
# ============================================================
def _extract_json_from_text(text: str) -> Optional[Any]:
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        frag = text[start:end+1]
        try:
            return json.loads(frag)
        except Exception:
            frag2 = frag.replace("'", '"')
            try:
                return json.loads(frag2)
            except Exception:
                return None
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1:
        frag = text[start:end+1]
        try:
            return json.loads(frag)
        except Exception:
            frag2 = frag.replace("'", '"')
            try:
                return json.loads(frag2)
            except Exception:
                return None
    return None


# ============================================================
# Generowanie pytań dla testu
# ============================================================
def generate_questions_for_categories(
    test: Test,
    per_category: int = 3,
    model: str = "gpt-3.5-turbo"
) -> Dict[str, List[Questions]]:
    """
    Generuje pytania do testu predyspozycji na podstawie kategorii.
    Jeśli pytanie istnieje w bazie -> przypisuje istniejące,
    jeśli nie -> tworzy nowe pytanie.
    """
    categories = list(CategoryCourse.objects.values_list("name", flat=True)) + \
                 list(CategoryEmploy.objects.values_list("name", flat=True))
    categories = list(dict.fromkeys(categories))  # unikalne

    results: Dict[str, List[Questions]] = {}

    for category in categories:
        system_msg = (
            "Jesteś ekspertem HR i edukacji. Twoim zadaniem jest tworzenie pytań "
            "do testu predyspozycji zawodowych i edukacyjnych."
        )
        user_msg = (
            f"Wygeneruj {per_category} różne pytania testowe sprawdzające "
            f"predyspozycje użytkownika w kategorii: {category}. "
            f"Zwróć wyłącznie w formacie JSON: "
            f"[{{'question': '...', 'correct': 'TAK/ NIE'}}]"
        )

        try:
            resp = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.7,
                max_tokens=500,
            )
            text = resp["choices"][0]["message"]["content"]
            parsed = _extract_json_from_text(text)

            if not parsed or not isinstance(parsed, list):
                continue

            results[category] = []

            with transaction.atomic():
                for item in parsed:
                    q_text = item.get("question")
                    correct = item.get("correct", "TAK")

                    if not q_text:
                        continue

                    # sprawdzamy czy istnieje takie pytanie
                    existing = Questions.objects.filter(question=q_text).first()
                    if existing:
                        q_obj = existing
                    else:
                        q_obj = Questions.objects.create(
                            question=q_text,
                            correct=correct,
                            test=test
                        )
                    results[category].append(q_obj)

        except Exception as e:
            print(f"[OpenAI ERROR][{category}] {e}")
            continue

    return results


# ============================================================
# Liczenie predyspozycji przy pomocy OpenAI
# ============================================================
def compute_trait_scores_openai(
    answers: List[Dict[str, Any]],
    model: str = "gpt-3.5-turbo",
    max_retries: int = 2,
) -> Dict[str, float]:
    """
    Zwraca {kategoria: score 0..1} na podstawie odpowiedzi użytkownika.
    Kategorie pobierane są z CategoryCourse + CategoryEmploy.
    """
    categories = list(CategoryCourse.objects.values_list("name", flat=True)) + \
                 list(CategoryEmploy.objects.values_list("name", flat=True))
    categories = list(dict.fromkeys(categories))  # unikalne

    system_msg = (
        "Jesteś asystentem oceniającym predyspozycje użytkownika. "
        "Dla każdej podanej kategorii przypisz wynik 0..1. "
        "Zwróć wyłącznie JSON w formacie {\"Kategoria\": 0.85, ...}."
    )
    user_msg = (
        f"Kategorie: {categories}\n\n"
        f"Odpowiedzi użytkownika:\n{json.dumps(answers, ensure_ascii=False)}"
    )

    for attempt in range(max_retries+1):
        try:
            resp = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.0,
                max_tokens=600,
            )
            text = resp["choices"][0]["message"]["content"]
            parsed = _extract_json_from_text(text)
            if not parsed:
                raise ValueError("Nie udało się sparsować JSON z odpowiedzi OpenAI")

            scores = {}
            for k, v in parsed.items():
                try:
                    val = float(v)
                    if val > 1:
                        val = val / 100 if val <= 100 else 1.0
                except Exception:
                    val = 0.5
                scores[k] = max(0.0, min(1.0, val))

            for cat in categories:
                if cat not in scores:
                    scores[cat] = 0.0
            return scores
        except Exception:
            if attempt == max_retries:
                return {c: 0.5 for c in categories}
            time.sleep(1.5 * (attempt+1))


# ============================================================
# Adaptacja pytań + wybór kategorii
# ============================================================
def adapt_questions_fuzzy(
    user_id: int,
    use_openai: bool = True,
    openai_model: str = "gpt-3.5-turbo",
) -> Dict[str, Any]:
    """
    - Pobiera odpowiedzi użytkownika z Answers,
    - Liczy predyspozycje (trait_scores),
    - Ustawia difficulty pytań,
    - Zwraca najlepszą kategorię + kursy i oferty pracy.
    """
    # --- Pobranie odpowiedzi użytkownika ---
    answers_qs: QuerySet = Answers.objects.filter(user_id=user_id).select_related("question")
    user_answers = [{"question": a.question.question, "answer": a.answer} for a in answers_qs]

    # --- Obliczenie predyspozycji ---
    if use_openai:
        trait_scores = compute_trait_scores_openai(user_answers, model=openai_model)
    else:
        all_cats = list(CategoryCourse.objects.values_list("name", flat=True)) + \
                   list(CategoryEmploy.objects.values_list("name", flat=True))
        trait_scores = {c: 0.5 for c in all_cats}

    # --- Adaptacja pytań ---
    out_questions = []
    all_questions = Questions.objects.all()
    if not SKFUZZY_AVAILABLE:
        for q in all_questions:
            pred = getattr(q.test.subject.course.category, "name", None)
            score = trait_scores.get(pred, 0.5)
            if score > 0.7:
                diff = "trudny"
            elif score < 0.3:
                diff = "łatwy"
            else:
                diff = "średni"
            out_questions.append({"id": q.id, "question": q.question, "difficulty": diff})
    else:
        x = np.arange(0, 1.01, 0.01)
        low = fuzz.trimf(x, [0.0, 0.0, 0.5])
        med = fuzz.trimf(x, [0.0, 0.5, 1.0])
        high = fuzz.trimf(x, [0.5, 1.0, 1.0])
        for q in all_questions:
            pred = getattr(q.test.subject.course.category, "name", None)
            score = trait_scores.get(pred, 0.5)
            l = fuzz.interp_membership(x, low, score)
            m = fuzz.interp_membership(x, med, score)
            h = fuzz.interp_membership(x, high, score)
            if h >= m and h >= l:
                diff = "trudny"
            elif l >= m and l >= h:
                diff = "łatwy"
            else:
                diff = "średni"
            out_questions.append({"id": q.id, "question": q.question, "difficulty": diff})

    # --- Najlepsza kategoria ---
    sorted_traits = sorted(trait_scores.items(), key=lambda x: x[1], reverse=True)
    top_score = sorted_traits[0][1]
    top_categories = [cat for cat, s in sorted_traits if abs(s-top_score) < 1e-9]

    if len(top_categories) == 1:
        best_cat = top_categories[0]
    else:
        counts = {c: OffersJob.objects.filter(category__name=c).count() for c in top_categories}
        best_cat = max(counts, key=counts.get)

    # --- Kursy i oferty pracy ---
    courses_qs = Course.objects.filter(category__name=best_cat)
    jobs_qs = OffersJob.objects.filter(category__name=best_cat)

    courses = [{"id": c.id, "title": c.title} for c in courses_qs]
    jobs = [{"id": j.id, "title": j.title, "business": j.business.name} for j in jobs_qs]

    return {
        "questions": out_questions,
        "category": best_cat,
        "courses": courses,
        "jobs": jobs,
    }


# ============================================================
# Całościowy pipeline: generowanie + analiza
# ============================================================
def prepare_and_adapt_test(
    test: Test,
    user_id: int,
    per_category: int = 3,
    use_openai: bool = True,
    openai_model: str = "gpt-3.5-turbo",
) -> Dict[str, Any]:
    """
    - Generuje pytania do testu (jeśli nie istnieją),
    - Liczy predyspozycje,
    - Ustawia difficulty,
    - Zwraca kategorię + kursy i oferty pracy.
    """
    generate_questions_for_categories(test, per_category=per_category, model=openai_model)
    return adapt_questions_fuzzy(user_id, use_openai=use_openai, openai_model=openai_model)

@csrf_exempt
def generate_questions_view(request, test_id: int):
    """
    Widok: generowanie pytań dla testu.
    GET/POST -> zwraca pytania.
    """
    if request.method == "POST":
        body = json.loads(request.body.decode("utf-8"))
        per_category = body.get("per_category", 3)
        model = body.get("model", "gpt-3.5-turbo")
    else:
        per_category = int(request.GET.get("per_category", 3))
        model = request.GET.get("model", "gpt-3.5-turbo")

    try:
        test = Test.objects.get(pk=test_id)
    except Test.DoesNotExist:
        return HttpResponse({"error": "Test not found"}, status=404)

    results = generate_questions_for_categories(test, per_category=per_category, model=model)
#   return JsonResponse({"status": "ok", "categories": list(results.keys())})redirect('detect_bee')
    return redirect('detect_bee')

@csrf_exempt
def adapt_questions_view(request, user_id: int):
    """
    Widok: adaptacja pytań i wybór kategorii.
    """
    if request.method == "POST":
        body = json.loads(request.body.decode("utf-8"))
        use_openai = body.get("use_openai", True)
        model = body.get("model", "gpt-3.5-turbo")
    else:
        use_openai = request.GET.get("use_openai", "true").lower() == "true"
        model = request.GET.get("model", "gpt-3.5-turbo")

    result = adapt_questions_fuzzy(user_id, use_openai=use_openai, openai_model=model)
#   return JsonResponse(result, safe=False)
    return redirect('detect_bee')


@csrf_exempt
def prepare_and_adapt_view(request, test_id: int, user_id: int):
    """
    Widok: całościowy pipeline -> generowanie + analiza.
    """
    if request.method == "POST":
        body = json.loads(request.body.decode("utf-8"))
        per_category = body.get("per_category", 3)
        use_openai = body.get("use_openai", True)
        model = body.get("model", "gpt-3.5-turbo")
    else:
        per_category = int(request.GET.get("per_category", 3))
        use_openai = request.GET.get("use_openai", "true").lower() == "true"
        model = request.GET.get("model", "gpt-3.5-turbo")

    try:
        test = Test.objects.get(pk=test_id)
    except Test.DoesNotExist:
        return HttpResponse({"error": "Test not found"}, status=404)

    result = prepare_and_adapt_test(
        test,
        user_id,
        per_category=per_category,
        use_openai=use_openai,
        openai_model=model,
    )
#   return JsonResponse(result, safe=False)
    return redirect('detect_bee')

# Algorytm AI: 1. Dane testowe. 2. Dane treningowe. 3. Wynik.