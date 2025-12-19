from itertools import chain
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.db import transaction
from django.db.models import Q, Count, Case, When
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView, UpdateView, DeleteView
from django.template.loader import get_template
from django.views import View
from django.utils import timezone
from django.contrib.auth import login
from django.template import TemplateDoesNotExist
import logging
from django.http import HttpResponse, Http404, HttpResponseNotFound
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from .models import CV, HR, Opinion, TagBusiness, TagPortfolio, TagCourse, Test, Portfolio, Projects, Link, Experience, CategoryCourse, CategoryEmploy, Certificate, Course, OffersJob, OffersJobUser, Business, Subject, TestScore, Answers, Questions, Hobby, Skills, Education, Questionnaire, Transmition, Comment
from .forms import CVForm, OpinionForm, HRForm, SubjectForm, AddOfferJobUserForm, UpdateOfferJobUserForm, AnswerForm, CourseForm, TestForm, LinkForm, ProjectForm, BusinessForm, QuestionForm, OfferJobsForm, PortfolioForm, ExperienceForm, QuestionFormSet, ExperienceFormSet, LinkFormSet, ProjectsFormSet, SubjectFormSet, QuestionnaireForm, HobbyForm, SkillsForm, EducationForm, EducationFormSet, SkillsFormSet, HobbyFormSet, TransmitionForm, CommentForm
#from .utils import rsa_encrypt, pq_encrypt
# Create your views here.

logger = logging.getLogger(__name__)

def check_template(template_name, request):
    try:
        get_template(template_name)
        logger.info(f"Template '{template_name}' found.")
        return True
    except TemplateDoesNotExist:
        logger.error(f"Template '{template_name}' does not exist for {request.path}")
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

class AddHRView(LoginRequiredMixin, View):
    template_name = 'add_hr.html'
    form_class = HRForm

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        business_id = self.kwargs.get('business_id')
        business = get_object_or_404(Business, id=business_id)

        # Check if HR already exists for this user
        hr, created = HR.objects.get_or_create(
            user=request.user,
            defaults={
                'first_name': form.data.get('first_name'),
                'last_name': form.data.get('last_name'),
                'email': form.data.get('email'),
                'number_phone': form.data.get('number_phone'),
            }
        )

        # Update fields if HR existed but info has changed
        if not created:
            hr.first_name = form.data.get('first_name')
            hr.last_name = form.data.get('last_name')
            hr.email = form.data.get('email')
            hr.number_phone = form.data.get('number_phone')
            hr.save()

        # Link business
        hr.business.add(business)

        # Redirect to success
        return redirect('add_offer_jobs', business_id=business.id, hr_id=hr.id)

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
        hr = get_object_or_404(HR, id=hr_id, user=self.request.user)
        # Check if user's HR is associated with this business (M2M relationship)
        if not hr.business.filter(id=business_id).exists():
            raise Http404("Business not found for this HR")
        return hr

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
        business = get_object_or_404(Business, id=business_id)
        # Security: Check if user has HR access to this business
        if not business.hr_set.filter(user=self.request.user).exists():
            raise Http404("You don't have permission to edit this business")
        return business

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

    def delete(self, request, *args, **kwargs):
        offer = self.get_object()
        if offer.hr.user != self.request.user:
            messages.error(self.request, "Nie masz uprawnień do usunięcia tej oferty.")
            return redirect('offers_job_created_by_user')
        return super().delete(request, *args, **kwargs)

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

class AddSubjectView(LoginRequiredMixin, View):
    template_name = 'add_subject.html'

    def get(self, request, *args, **kwargs):
        formset = SubjectFormSet(queryset=Subject.objects.none())
        return render(request, self.template_name, {
            'formset': formset,
            'course_id': self.kwargs['course_id'],
        })

    def post(self, request, *args, **kwargs):
        formset = SubjectFormSet(request.POST, request.FILES)

        if formset.is_valid():
            for form in formset:
                if not form.has_changed():
                    continue

                instance = form.save(commit=False)
                instance.course_id = self.kwargs['course_id']
                instance.save()

            return redirect('subject_to_course_view', course_id=self.kwargs['course_id'])

        return render(request, self.template_name, {
            'formset': formset,
            'course_id': self.kwargs['course_id'],
        })

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)


class UpdateSubjectView(LoginRequiredMixin, UpdateView):
    model = Subject
    form_class = SubjectForm
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
    template_name = 'add_question.html'
    
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
        # Get HR profile for current user
        hr = HR.objects.get(user=request.user)
        
        if query:
            # Filter businesses assigned to current user's HR profile
            businesses = hr.business.filter(Q(name__icontains=query))
            tags = TagBusiness.objects.filter(Q(name__icontains=query))
        else:
            # Get all businesses assigned to current user's HR profile
            businesses = hr.business.all()

        logger.info(f"Business and tags retrieved successfully for user {request.user}. Query: '{query}'")
    except HR.DoesNotExist:
        logger.warning(f"HR profile not found for user {request.user}.")
        return HttpResponse("No HR profile found for this user.", status=404)
    except Exception as e:
        logger.error(f"Error retrieving businesses or tags for user {request.user}: {e}")
        return HttpResponse("An error occurred while retrieving data.", status=500)

    # Można też połączyć wyniki (jeśli chcesz wyświetlać jako jedna lista)
    products = list(chain(businesses, tags))

    return render(request, template_name, {
        'products': products,
        'query': query,
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
    tags_id = request.GET.get('tags')
    tags = TagBusiness.objects.all()
    products = []

    try:
        offers_query = OffersJob.objects.all()

        if query:
            offers_query = offers_query.filter(Q(title__icontains=query))

        if category_id:
            offers_query = offers_query.filter(category_id=category_id)

        if tags_id:
            offers_query = offers_query.filter(tags_id=tags_id)

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
        'tags': tags,
        'categories': categories,
        'selected_category': category_id,
    })

@transaction.atomic
def accepted_offers_job_user(request):
    template_name = 'accepted_offers_job_user.html'
    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")

    try:
        user = request.user
        transmitions = Transmition.objects.filter(
            Q(leaders=user) | Q(participants=user)
        ).distinct()
        # annotate transmitions with is_live flag
        now = timezone.now()
        for t in transmitions:
            try:
                t.is_live = (t.start <= now and now <= t.end)
            except Exception:
                t.is_live = False

        products = OffersJobUser.objects.filter(is_accept=True, user=user).select_related('offer__business', 'offer__hr')
        logger.info(f"Products retrieved successfully for user {request.user}.")
    except Exception as e:
        logger.error(f"Error retrieving categories for user {request.user}: {e}")
        products = []
        return HttpResponse("An error occurred while retrieving categories.", status=500)
    
    return render(request, template_name, {'products': products, 'transmitions': transmitions})

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
@login_required
def hr_to_business_view(request, business_id=None):
    template_name = 'hr_business_list.html'

    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")

    try:
        hr = HR.objects.get(user=request.user)
        # If business_id provided, ensure it's one of HR's businesses
        if business_id:
            businesses = hr.business.filter(id=business_id)
        else:
            businesses = hr.business.all()
        logger.info(f"Businesses retrieved successfully for HR {hr}.")
    except HR.DoesNotExist:
        logger.warning(f"HR profile not found for user {request.user}.")
        return HttpResponse("No HR profile found for this user.", status=404)
    except Exception as e:
        logger.exception(f"Unexpected error while retrieving businesses for user {request.user}: {e}")
        return HttpResponse("An error occurred while retrieving businesses.", status=500)

    return render(request, template_name, {'businesses': businesses, 'user': request.user})

@transaction.atomic
@login_required
def search_course_view(request):
    template_name = 'search_course.html'

    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")

    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category')
    tags_id = request.GET.get('tags')
    categories = CategoryCourse.objects.all()
    courses = []
    tags = TagCourse.objects.all()

    try:
        course_query = Course.objects.all()

        if query:
            course_query = course_query.filter(Q(title__icontains=query))

        if category_id:
            course_query = course_query.filter(category_id=category_id)

        if tags_id:
            course_query = course_query.filter(tags_id=tags_id)

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
        opinion = Opinion.objects.filter(
            course=course
        )
        products = Subject.objects.filter(course=course)
        logger.info(f"Subjects retrieved successfully for Course {course.title} by user {request.user}.")
    except Exception as e:
        logger.exception(f"Error retrieving subjects for course {course_id} by user {request.user}: {e}")
        return HttpResponse("An error occurred while retrieving subjects.", status=500)

    return render(request, template_name, {'course': course,'products': products,'opinion': opinion})

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
def test_to_question_view(request, course_id, subject_id, test_id):
    template_name = 'questions_list.html'

    if not check_template(template_name, request):
        logger.warning(
            f"Template '{template_name}' not found for user {request.user}."
        )
        return HttpResponseNotFound("Template not found.")

    try:
        test = get_object_or_404(
            Test,
            id=test_id,
            subject__id=subject_id,
            subject__course__id=course_id
        )
        products = Questions.objects.filter(test=test)
        logger.info(
            f"Questions for test '{test.title}' retrieved successfully by user {request.user}."
        )
    except Exception as e:
        logger.error(
            f"Error retrieving questions for test ID {test_id}: {e}"
        )
        return HttpResponse(
            "An error occurred while retrieving questions.",
            status=500
        )

    return render(request, template_name, {
        'products': products,
    })

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
    tags = TagPortfolio.objects.all()
    tags_id = request.GET.get('tags')

    try:
        portfolios_all = Portfolio.objects.all()

        if query:
            portfolios_all = portfolios_all.filter(Q(title__icontains=query))

        if tags_id:
            portfolios_all = portfolios_all.filter(tags_id=tags_id)

        portfolios = portfolios_all

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
    query = request.GET.get('q', '').strip()

    if query:
        cvs = CV.objects.filter(title__icontains=query)
    else:
        cvs = CV.objects.all()

    return render(request, "search_cv.html", {
        "query": query,
        "cvs": cvs
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

@transaction.atomic
def comments_transmition_view(request, transmition_id):
    template_name = 'transmition_view.html'
    
    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")
    
    try:
        portfolio = get_object_or_404(Transmition, id=transmition_id)
        links = Comment.objects.filter(portfolio=portfolio)
        logger.info(f"Links retrieved successfully for portfolio {transmition_id} by user {request.user}.")
    except Exception as e:
        logger.error(f"Error retrieving links for portfolio {transmition_id} by user {request.user}: {e}")
        return HttpResponse("An error occurred while retrieving links.", status=500)
    
    return render(request, template_name, {'comments': links, "now": timezone.now()})

class AddTransmitionView(LoginRequiredMixin, CreateView):
    form_class = TransmitionForm
    template_name = 'add_transmition.html'

    def form_valid(self, form):
        form.instance.leaders = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('index')

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)


class UpdateTransmitionView(LoginRequiredMixin, UpdateView):
    model = Transmition
    form_class = TransmitionForm
    template_name = 'update_transmition.html'

    def get_object(self, queryset=None):
        course_id = self.kwargs.get('transmition_id')
        return get_object_or_404(Transmition, id=course_id, author=self.request.user)

    def get_success_url(self):
        return reverse('index')

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)


class DeleteTransmitionView(LoginRequiredMixin, DeleteView):
    model = Transmition
    template_name = 'delete_transmition.html'

    def get_object(self, queryset=None):
        course_id = self.kwargs.get('transmition_id')
        return get_object_or_404(Transmition, id=course_id, author=self.request.user)

    def get_success_url(self):
        return reverse('index')

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)
    
class AddCommentView(LoginRequiredMixin, CreateView):
    form_class = CommentForm
    template_name = 'add_comments.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.transmition = Transmition.objects.get(pk=self.kwargs['transmition_id'])
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('transmition_view', kwargs={'transmition_id': self.object.transmition.id})

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)


class UpdateCommentView(LoginRequiredMixin, UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = 'update_comment.html'

    def get_object(self, queryset=None):
        course_id = self.kwargs.get('transmition_id')
        comment_id = self.kwargs.get('comment_id')
        return get_object_or_404(Comment, id=comment_id, transmition=course_id, author=self.request.user)

    def get_success_url(self):
        return reverse('transmition_view', kwargs={'transmition_id': self.object.transmition.id})

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)
    
class DeleteCommentView(LoginRequiredMixin, DeleteView):
    model = Comment
    template_name = 'delete_comment.html'

    def get_object(self, queryset=None):
        course_id = self.kwargs.get('transmition_id')
        comment_id = self.kwargs.get('comment_id')
        return get_object_or_404(Comment, id=comment_id, transmition=course_id, author=self.request.user)

    def get_success_url(self):
        return reverse('transmition_view', kwargs={'transmition_id': self.object.transmition.id})

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)
    
class AddOpinionView(LoginRequiredMixin, CreateView):
    form_class = OpinionForm
    template_name = 'add_opinion.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.course = Course.objects.get(pk=self.kwargs['course_id'])
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('subject_to_course_view', kwargs={'course_id': self.object.course.id})

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)


class UpdateOpinionView(LoginRequiredMixin, UpdateView):
    model = Opinion
    form_class = OpinionForm
    template_name = 'update_opinion.html'

    def get_object(self, queryset=None):
        course_id = self.kwargs.get('course_id')
        comment_id = self.kwargs.get('opinion_id')
        return get_object_or_404(Opinion, id=comment_id, course=course_id, author=self.request.user)

    def get_success_url(self):
        return reverse('subject_to_course_view', kwargs={'course_id': self.object.course.id})

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)
    
class DeleteOpinionView(LoginRequiredMixin, DeleteView):
    model = Opinion
    template_name = 'delete_opinion.html'

    def get_object(self, queryset=None):
        course_id = self.kwargs.get('course_id')
        comment_id = self.kwargs.get('opinion_id')
        return get_object_or_404(Opinion, id=comment_id, course=course_id, author=self.request.user)

    def get_success_url(self):
        return reverse('subject_to_course_view', kwargs={'course_id': self.object.course.id})

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)
