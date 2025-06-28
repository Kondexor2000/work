from itertools import chain
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.db import transaction
from django.db.models import Q
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView, UpdateView, DeleteView
from django.shortcuts import redirect, render
from django.template.loader import get_template
from django.template import TemplateDoesNotExist
import logging
from django.http import HttpResponse, Http404, HttpResponseNotFound
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from .models import CV, HR, TagBusiness, TagPortfolio, TagCourse, Test, Portfolio, Projects, Link, Experience, CategoryCourse, CategoryEmploy, Certificate, Course, OffersJob, OffersJobUser, Business, Subject, TestScore, Answers, Questions 
from .forms import CVForm, HRForm, SubjectForm, AddOfferJobUserForm, UpdateOfferJobUserForm, AnswerForm, CourseForm, TestForm, LinkForm, ProjectForm, BusinessForm, QuestionForm, OfferJobsForm, PortfolioForm, ExperienceForm
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
    success_url = reverse_lazy('login')

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Template not found.")
        if request.user.is_authenticated:
            messages.info(request, "You are already registered and logged in.")
            return redirect('add-post')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Registration successful. Please log in.")
        return response

class EditProfileView(LoginRequiredMixin, UpdateView):
    form_class = UserChangeForm
    template_name = 'edit_profile.html'
    success_url = reverse_lazy('add-course')

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
        return reverse_lazy('add_course')

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
        return reverse('add_offer_jobs')

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


# === OffersJob ===

class AddOfferJobsView(LoginRequiredMixin, CreateView):
    form_class = OfferJobsForm
    template_name = 'add_offer_jobs.html'

    def form_valid(self, form):
        if HR.objects.filter(user=self.request.user).exists():
            form.add_error(None, "You already have an HR profile.")
            return self.form_invalid(form)

        business_id = self.kwargs.get('business_id')
        business = get_object_or_404(Business, id=business_id)

        form.instance.user = self.request.user
        response = super().form_valid(form)
        form.instance.business.set([business])
        return response

    def get_success_url(self):
        # Redirect to the same add offer page (for multiple entries)
        return reverse('add_offer_jobs', kwargs={
            'business_id': self.kwargs.get('business_id'),
            'hr_id': self.kwargs.get('hr_id'),
        })

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)


class DeleteOffersJobsView(LoginRequiredMixin, DeleteView):
    model = OffersJob
    template_name = 'delete_offer_jobs.html'

    def get_object(self, queryset=None):
        offer_jobs_id = self.kwargs.get('offer_jobs_id')
        return get_object_or_404(OffersJob, id=offer_jobs_id, user=self.request.user)

    def delete(self, request, *args, **kwargs):
        offer = self.get_object()
        if offer.user == self.request.user:
            return super().delete(request, *args, **kwargs)
        messages.error(request, "Nie masz uprawnień do usunięcia tej oferty.")
        return redirect('search_portfolio')

    def get_success_url(self):
        return reverse('search_portfolio')

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
        return reverse('search_offers_job', kwargs={'user_pk': self.request.user.pk})

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
        return reverse('search_offers_job', kwargs={'user_pk': self.request.user.pk})

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
    form_class = SubjectForm
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
    form_class = SubjectForm
    template_name = 'update_subject.html'

    def get_object(self, queryset=None):
        subject_id = self.kwargs.get('subject_id')
        return get_object_or_404(Subject, id=subject_id, user=self.request.user)

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
        subject_id = self.kwargs.get('subject_id')
        return get_object_or_404(Subject, id=subject_id, user=self.request.user)

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
        test_id = self.kwargs.get('test_id')
        return get_object_or_404(Test, id=test_id, user=self.request.user)

    def get_success_url(self):
        return reverse('test_to_question_view', kwargs={'user_pk': self.request.user.pk})

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)


class DeleteTestView(LoginRequiredMixin, DeleteView):
    model = Test
    template_name = 'delete_test.html'

    def get_object(self, queryset=None):
        test_id = self.kwargs.get('test_id')
        return get_object_or_404(Test, id=test_id, user=self.request.user)

    def get_success_url(self):
        return reverse('add_test', kwargs={'user_pk': self.request.user.pk})

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)


# === QUESTIONS ===

class AddQuestionView(LoginRequiredMixin, CreateView):
    form_class = QuestionForm
    template_name = 'add_question.html'

    def form_valid(self, form):
        form.instance.test_id = self.kwargs['test_id']  # <-- ustawienie relacji z Test
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('subject_to_course_view', args=[self.kwargs['course_id']])  # jeśli nie potrzebujesz ID, może zostać

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)


class UpdateQuestionView(LoginRequiredMixin, UpdateView):
    model = Questions
    form_class = QuestionForm
    template_name = 'update_question.html'

    def get_object(self, queryset=None):
        question_id = self.kwargs.get('question_id')
        return get_object_or_404(Questions, id=question_id, user=self.request.user)

    def get_success_url(self):
        return reverse('test_to_question_view', kwargs={'user_pk': self.request.user.pk})

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)


class DeleteQuestionView(LoginRequiredMixin, DeleteView):
    model = Questions
    template_name = 'delete_question.html'

    def get_object(self, queryset=None):
        question_id = self.kwargs.get('question_id')
        return get_object_or_404(Questions, id=question_id, user=self.request.user)

    def get_success_url(self):
        return reverse('add_question', kwargs={'user_pk': self.request.user.pk})

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)


# === ANSWERS ===

class AddAnswersView(LoginRequiredMixin, CreateView):
    form_class = AnswerForm
    template_name = 'add_answers.html'
    success_url = reverse_lazy('search_stores')  # fallback

    @transaction.atomic
    def form_valid(self, form):
        form.instance.user = self.request.user
        question = form.cleaned_data.get('question')
        answer_text = form.cleaned_data.get('answer').strip().lower()
        correct_answer = question.correct.strip().lower()
        test = question.test

        test_score, _ = TestScore.objects.get_or_create(user=self.request.user, test=test, defaults={'score': 0, 'minimum': 0})

        if answer_text == correct_answer:
            test_score.score += 1
            test_score.save()

        form.instance.question = question
        form.save()

        next_question = Questions.objects.filter(test=test, id__gt=question.id).order_by('id').first()
        if next_question:
            return redirect('answer_question', course_id=test.subject.course.id, subject_id=test.subject.id, test_id=test.id, question_id=next_question.id)
        else:
            return redirect('search_stores', subject_id=test.subject.id)

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
        return reverse('portfolio_to_user_view', kwargs={'user_pk': self.request.user.pk})

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)


# === Project ===

class AddProjectView(LoginRequiredMixin, CreateView):
    form_class = ProjectForm
    template_name = 'add_project.html'

    def form_valid(self, form):
        portfolio_id = self.kwargs.get('portfolio_id')
        portfolio = get_object_or_404(Portfolio, id=portfolio_id, user=self.request.user)
        form.instance.user = self.request.user
        form.instance.portfolio = portfolio
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('my_portfolio_projects_view', kwargs={'portfolio_id': self.kwargs['portfolio_id']})

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)


class UpdateProjectView(LoginRequiredMixin, UpdateView):
    model = Projects
    form_class = ProjectForm
    template_name = 'update_project.html'

    def get_object(self, queryset=None):
        portfolio_id = self.kwargs.get('portfolio_id')
        project_id = self.kwargs.get('project_id')
        return get_object_or_404(Projects, id=project_id, portfolio__id=portfolio_id, portfolio__user=self.request.user)

    def get_success_url(self):
        return reverse('my_portfolio_projects_view', kwargs={'user_pk': self.request.user.pk})

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)


# === Link ===

class AddLinkView(LoginRequiredMixin, CreateView):
    form_class = LinkForm
    template_name = 'add_link.html'

    def form_valid(self, form):
        portfolio_id = self.kwargs.get('portfolio_id')
        portfolio = get_object_or_404(Portfolio, id=portfolio_id, user=self.request.user)
        form.instance.user = self.request.user
        form.instance.portfolio = portfolio
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('my_portfolio_links_view')

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)


class UpdateLinkView(LoginRequiredMixin, UpdateView):
    model = Link
    form_class = LinkForm
    template_name = 'update_link.html'

    def get_object(self, queryset=None):
        portfolio_id = self.kwargs.get('portfolio_id')
        link_id = self.kwargs.get('link_id')
        return get_object_or_404(Link, id=link_id, portfolio__id=portfolio_id, portfolio__user=self.request.user)

    def get_success_url(self):
        return reverse('my_portfolio_links_view', kwargs={'user_pk': self.request.user.pk})

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
        return reverse('cv_to_user_view', kwargs={'user_pk': self.request.user.pk})

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)


# === EXPERIENCE ===

class AddExperienceView(LoginRequiredMixin, CreateView):
    form_class = ExperienceForm
    template_name = 'add_experience.html'
    success_url = reverse_lazy('my_cv_experience_view')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)


class UpdateExperienceView(LoginRequiredMixin, UpdateView):
    model = Experience
    form_class = ExperienceForm
    template_name = 'update_experience.html'

    def get_object(self, queryset=None):
        cv_id = self.kwargs.get('cv_id')
        return get_object_or_404(Experience, id=cv_id, cv__user=self.request.user)

    def get_success_url(self):
        return reverse('my_cv_experience_view', kwargs={'user_pk': self.request.user.pk})

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
    products = []

    try:
        if query:
            products = OffersJob.objects.filter(Q(title__icontains=query))
        else:
            products = OffersJob.objects.all()

        logger.info(f"Offers retrieved successfully for user {request.user}. Query: '{query}'")
    except Exception as e:
        logger.error(f"Error retrieving offers for user {request.user}: {e}")
        return HttpResponse("An error occurred while retrieving offers.", status=500)

    return render(request, template_name, {'products': products, 'query': query})

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
def category_employ_view(request):
    template_name = 'category_employ_list.html'
    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")

    try:
        products = CategoryEmploy.objects.all()
        logger.info(f"Products retrieved successfully for user {request.user}.")
    except Exception as e:
        logger.error(f"Error retrieving categories for user {request.user}: {e}")
        products = []
        return HttpResponse("An error occurred while retrieving categories.", status=500)
    
    return render(request, template_name, {'products': products})

@transaction.atomic
def category_course_view(request):
    template_name = 'category_course_list.html'
    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")

    try:
        products = CategoryCourse.objects.all()
        logger.info(f"Products retrieved successfully for user {request.user}.")
    except Exception as e:
        logger.error(f"Error retrieving categories for user {request.user}: {e}")
        products = []
        return HttpResponse("An error occurred while retrieving categories.", status=500)
    
    return render(request, template_name, {'products': products})

@transaction.atomic
@login_required
def search_course_view(request):
    template_name = 'search_course.html'

    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")

    query = request.GET.get('q', '').strip()
    courses = []
    tags = []

    try:
        if query:
            courses = Course.objects.filter(Q(title__icontains=query))
            tags = TagCourse.objects.filter(Q(name__icontains=query))
        else:
            courses = Course.objects.all()

        logger.info(f"Courses and tags retrieved successfully for user {request.user}. Query: '{query}'")
    except Exception as e:
        logger.error(f"Error retrieving courses or tags for user {request.user}: {e}")
        return HttpResponse("An error occurred while retrieving data.", status=500)

    return render(request, template_name, {
        'courses': courses,
        'tags': tags,
        'query': query
    })

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
def subject_to_test_view(request, subject_id):
    template_name = 'test_list.html'
    
    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")

    try:
        subject = get_object_or_404(Subject, id=subject_id)
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
    
    return render(request, template_name, {'products': experiences})

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