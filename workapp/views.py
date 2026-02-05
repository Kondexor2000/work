from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.db import transaction
from django.db.models import Q
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
from .models import Opinion, TagPortfolio, TagCourse, Portfolio, Link, CategoryCourse, Course, Subject, Transmition, Comment
from .forms import OpinionForm, SubjectForm,  CourseForm, PortfolioForm, LinkFormSet, SubjectFormSet, TransmitionForm, CommentForm
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
    
#Kurs
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
        return reverse('subject_to_course_view', kwargs={'course_id': self.kwargs['course_id']})

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
        return reverse('add_course')

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
        return get_object_or_404(Subject, id=subject_id, course=course_id)

    def get_success_url(self):
        return reverse('subject_to_course_view', kwargs={'course_id': self.kwargs['course_id']})

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
        return get_object_or_404(Subject, id=subject_id, course=course_id)

    def get_success_url(self):
        return reverse('add_subject', kwargs={'course_id': self.kwargs['course_id']})

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)

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


class UpdateLinkView(LoginRequiredMixin, DeleteView):
    model = Link
    template_name = 'update_link.html'

    def get_object(self, queryset=None):
        portfolio_id = self.kwargs.get('portfolio_id')
        link_id = self.kwargs.get('link_id')
        return get_object_or_404(Link, id=link_id, portfolio=portfolio_id, portfolio__user=self.request.user)

    def get_success_url(self):
        return reverse('my_portfolio_links_view')

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)

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

        logger.info(f"Products retrieved successfully for user {request.user}.")
    except Exception as e:
        logger.error(f"Error retrieving categories for user {request.user}: {e}")
        products = []
        return HttpResponse("An error occurred while retrieving categories.", status=500)
    
    return render(request, template_name, {'transmitions': transmitions})

@transaction.atomic
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

@transaction.atomic
def subject_to_course_view(request, course_id):
    template_name = 'subject_list.html'

    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")

    try:
        products = Subject.objects.filter(course=course_id)
        course = get_object_or_404(Course, id=course_id)
        opinion = Opinion.objects.filter(
            course=course
        )
        logger.info(f"Subjects retrieved successfully for Course {course.title} by user {request.user}.")
    except Exception as e:
        logger.exception(f"Error retrieving subjects for course {course_id} by user {request.user}: {e}")
        return HttpResponse("An error occurred while retrieving subjects.", status=500)

    return render(request, template_name, {'products': products,'course': course, 'opinion': opinion})


@transaction.atomic
def subject_to_course_id_view(request, course_id, subject_id):
    template_name = 'subject_list_id.html'

    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")

    try:
        products = get_object_or_404(Subject, id=subject_id, course=course_id)
        logger.info(f"Subjects retrieved successfully for Course {products.title} by user {request.user}.")
    except Exception as e:
        logger.exception(f"Error retrieving subjects for course {course_id} by user {request.user}: {e}")
        return HttpResponse("An error occurred while retrieving subjects.", status=500)

    return render(request, template_name, {'products': products})

@transaction.atomic
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
def thanking_view(request):
    template_name = 'thanks.html'
    return render(request, template_name)

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
