from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.db import transaction
from django.db.models import Q
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView, UpdateView, DeleteView
from django.template.loader import get_template
from django.views import View
from django.contrib.auth import login
from django.template import TemplateDoesNotExist
import logging
import datetime
from django.utils import timezone
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4
from io import BytesIO
from django.http import HttpResponse, Http404, HttpResponseNotFound
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from .models import Recruter, TagPortfolio, TestScore, Portfolio, Link, Test, Question, Transmition, Comment
from .forms import AnswerForm, QuestionForm, QuestionFormSet,TestForm, PortfolioForm, LinkFormSet, RecruterForm, TransmitionForm, CommentForm
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
    

class AddTestView(LoginRequiredMixin, CreateView):
    form_class = TestForm
    template_name = 'add_test.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('add_question', args=[self.object.id])

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
        return get_object_or_404(Test, id=test_id, author=self.request.user)

    def get_success_url(self):
        return reverse('test_read')

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)


class DeleteTestView(LoginRequiredMixin, DeleteView):
    model = Test
    template_name = 'delete_test.html'

    def get_object(self, queryset=None):
        test_id = self.kwargs.get('test_id')
        return get_object_or_404(Test, id=test_id, author=self.request.user)

    def get_success_url(self):
        return reverse('test_read')

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)


# === SUBJECT ===

class AddQuestionView(LoginRequiredMixin, View):
    template_name = 'add_question.html'

    def get(self, request, *args, **kwargs):
        formset = QuestionFormSet(queryset=Question.objects.none())
        return render(request, self.template_name, {
            'formset': formset,
            'test_id': self.kwargs['test_id'],
        })

    def post(self, request, *args, **kwargs):
        formset = QuestionFormSet(request.POST, request.FILES)

        if formset.is_valid():
            for form in formset:
                if not form.has_changed():
                    continue

                instance = form.save(commit=False)
                instance.test_id = self.kwargs['test_id']
                instance.save()

            return redirect('question_read', test_id=self.kwargs['test_id'])

        return render(request, self.template_name, {
            'formset': formset,
            'test_id': self.kwargs['test_id'],
        })

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)


class UpdateQuestionView(LoginRequiredMixin, UpdateView):
    model = Question
    form_class = QuestionForm
    template_name = 'update_question.html'

    def get_object(self, queryset=None):
        test_id = self.kwargs.get('test_id')
        question_id = self.kwargs.get('question_id')
        return get_object_or_404(Question, id=question_id, test=test_id)

    def get_success_url(self):
        return reverse('question_read', kwargs={'test_id': self.kwargs['test_id']})

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)


class DeleteQuestionView(LoginRequiredMixin, DeleteView):
    model = Question
    template_name = 'delete_question.html'

    def get_object(self, queryset=None):
        test_id = self.kwargs.get('test_id')
        question_id = self.kwargs.get('question_id')
        return get_object_or_404(Question, id=question_id, test=test_id)

    def get_success_url(self):
        return reverse('add_question', kwargs={'test_id': self.kwargs['test_id']})

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)


class AddAnswerView(LoginRequiredMixin, CreateView):
    form_class = AnswerForm
    template_name = 'add_answer.html'

    def get_question(self):
        return get_object_or_404(Question, id=self.kwargs['question_id'])

    @transaction.atomic
    def form_valid(self, form):
        question = self.get_question()
        test = question.test
        user = self.request.user

        # sprawdź czy użytkownik jest zaproszony
        recruter = get_object_or_404(
            Recruter,
            candidate=user,
            test=test,
            finished=False
        )

        form.instance.user = user
        form.instance.question = question
        form.save()

        score_obj, _ = TestScore.objects.get_or_create(
            user=user,
            test=test,
            defaults={'max_score': test.question_set.count()}
        )

        if form.cleaned_data['answer'].strip().lower() == question.correct.strip().lower():
            score_obj.score += 1
            score_obj.save()

        next_question = Question.objects.filter(
            test=test,
            id__gt=question.id
        ).order_by('id').first()

        if next_question:
            return redirect('add_answer', question_id=next_question.id)

        # KONIEC TESTU
        score_obj.completed = True
        score_obj.completed_at = timezone.now()
        score_obj.save()

        recruter.finished = True
        recruter.save()

        return redirect('test_score', test_id=test.id)
    

class AddOfferJobsUserView(LoginRequiredMixin, CreateView):
    form_class = RecruterForm
    template_name = 'add_offer_jobs_user.html'

    def form_valid(self, form):
        form.instance.test.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('search_portfolio')

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

class DeletePortfolioView(LoginRequiredMixin, DeleteView):
    model = Portfolio
    template_name = 'delete_portfolio.html'

    def get_object(self, queryset=None):
        portfolio_id = self.kwargs.get('portfolio_id')
        return get_object_or_404(Portfolio, id=portfolio_id, user=self.request.user)

    def get_success_url(self):
        return reverse('portfolio_to_user_view')

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


class DeleteLinkView(LoginRequiredMixin, DeleteView):
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

        logger.info(f"Products retrieved successfully for user {request.user}.")
    except Exception as e:
        logger.error(f"Error retrieving categories for user {request.user}: {e}")
        return HttpResponse("An error occurred while retrieving categories.", status=500)
    
    return render(request, template_name, {'transmitions': transmitions})


@login_required
def generate_pdf_report(request, test_id):

    score = get_object_or_404(
        TestScore,
        user=request.user,
        test_id=test_id,
        completed=True
    )

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    percentage = round((score.score / score.max_score) * 100, 2) if score.max_score else 0
    status = "PASS" if percentage >= 60 else "FAIL"

    elements.append(Paragraph("Test Completion Report", styles["Heading1"]))
    elements.append(Spacer(1, 0.5 * inch))

    elements.append(Paragraph(f"Candidate: {request.user.username}", styles["Normal"]))
    elements.append(Paragraph(f"Test: {score.test.title}", styles["Normal"]))
    elements.append(Paragraph(f"Date: {score.completed_at.strftime('%Y-%m-%d %H:%M')}", styles["Normal"]))
    elements.append(Spacer(1, 0.5 * inch))

    data = [
        ["Score", f"{score.score} / {score.max_score}"],
        ["Percentage", f"{percentage}%"],
        ["Result", status],
    ]

    table = Table(data, colWidths=[2.5 * inch, 2.5 * inch])
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 1, colors.grey),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
    ]))

    elements.append(table)

    doc.build(elements)
    buffer.seek(0)

    return HttpResponse(
        buffer,
        content_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=report_{score.test.id}.pdf"},
    )

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
def recruter_to_user_view(request):
    template_name = 'recruter_user_list.html'
    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")

    try:
        products = Recruter.objects.filter(candidate=request.user, finished=False, test__is_finish=False)
        logger.info(f"Products retrieved successfully for user {request.user}.")
    except Exception as e:
        logger.error(f"Error retrieving categories for user {request.user}: {e}")
        products = []
        return HttpResponse("An error occurred while retrieving categories.", status=500)
    
    return render(request, template_name, {'products': products})

@transaction.atomic
def portfolio_to_id_view(request, portfolio_id):
    template_name = 'portfolio_id_list.html'
    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")

    try:
        products = get_object_or_404(Portfolio, id=portfolio_id)
        logger.info(f"Products retrieved successfully for user {request.user}.")
    except Exception as e:
        logger.error(f"Error retrieving categories for user {request.user}: {e}")
        products = []
        return HttpResponse("An error occurred while retrieving categories.", status=500)
    
    return render(request, template_name, {'products': products})

@transaction.atomic
def test_to_user_view(request):
    template_name = 'test_user_list.html'
    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")

    products = Test.objects.filter(author=request.user)
    
    return render(request, template_name, {'products': products})

@transaction.atomic
def thanking_view(request):
    template_name = 'thanks.html'
    return render(request, template_name)

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
def test_score_view(request, portfolio_id):
    template_name = 'test_score.html'
    
    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")
    
    try:
        portfolio = get_object_or_404(Test, id=portfolio_id)
        links = TestScore.objects.filter(portfolio=portfolio)
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
def test_questions_view(request, test_id):
    template_name = 'test_questions.html'
    
    if not check_template(template_name, request):
        logger.warning(f"Template '{template_name}' not found for user {request.user}.")
        return HttpResponseNotFound("Template not found.")
    
    portfolio = get_object_or_404(Test, id=test_id)
    links = Question.objects.filter(test=portfolio)
    
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
    
    return render(request, template_name, {'comments': links})

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
        return get_object_or_404(Transmition, id=course_id, leaders=self.request.user)

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