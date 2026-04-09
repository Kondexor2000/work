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
from django.core.paginator import Paginator
from langdetect import detect
import logging
import re
import datetime
from django.utils import timezone
from django.http import HttpResponse, Http404, HttpResponseNotFound
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from .models import TagPortfolio, Link
from .forms import LinkForm, LinkForm

# === Link ===

class AddLinkView(CreateView):
    form_class = LinkForm
    template_name = 'add_link.html'
    
    def get_success_url(self):
        return reverse('thanks')

"""
def accepted_offers_job_user(request):
    template_name = 'accepted_offers_job_user.html'

    user = request.user
    transmitions = Transmition.objects.filter(
        Q(leaders=user) | Q(participants=user)
    ).distinct()
        # annotate transmitions with is_live flag
    
    return render(request, template_name, {'transmitions': transmitions})
"""

def is_valid_text(text):
    try:
        text = text.strip()
        if not text or not text[0].isalpha():
            return False

        lang = detect(text)

        # tylko PL
        if lang not in ["pl"]:
            return False

        # dodatkowy filtr łacińskich końcówek
        latin_like = len(re.findall(r'\b\w+(us|um|ae|is)\b', text.lower()))

        return latin_like < 3

    except:
        return False

@transaction.atomic
def search_portfolio(request):
    template_name = 'search_portfolio.html'

    tags = TagPortfolio.objects.all()
    tags_id = request.GET.get('tags')

    portfolios = Link.objects.all().prefetch_related('tags').order_by('description')

    if tags_id and tags_id.isdigit():
        portfolios = portfolios.filter(tags__id=int(tags_id)).order_by('description')

    portfolio = list(portfolios)
    paginator = Paginator(portfolio, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, template_name, {
        'portfolios': page_obj,
        'tags': tags,
    })

def thanking_view(request):
    template_name = 'thanks.html'
    return render(request, template_name)

"""

def comments_transmition_view(request, transmition_id):
    template_name = 'transmition_view.html'
    
    portfolio = get_object_or_404(Transmition, id=transmition_id)
    links = Comment.objects.filter(transmition=portfolio)
    
    return render(request, template_name, {'comments': links, 'id': portfolio.id})

class AddTransmitionView(LoginRequiredMixin, CreateView):
    form_class = TransmitionForm
    template_name = 'add_transmition.html'

    def form_valid(self, form):
        form.instance.leaders = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('index')

class MixinTransmitionAuthor:
    def get_object(self, queryset=None):
        course_id = self.kwargs.get('transmition_id')
        return get_object_or_404(Transmition, id=course_id, leaders=self.request.user)

    def get_success_url(self):
        return reverse('index')

class TransmitionClassBase(LoginRequiredMixin):
    model = Transmition

class UpdateTransmitionView(MixinTransmitionAuthor, TransmitionClassBase, UpdateView):
    form_class = TransmitionForm
    template_name = 'update_transmition.html'

class DeleteTransmitionView(MixinTransmitionAuthor, TransmitionClassBase, DeleteView):
    template_name = 'delete_transmition.html'

class AddCommentView(LoginRequiredMixin, CreateView):
    form_class = CommentForm
    template_name = 'add_comments.html'

    def form_valid(self, form):

        transmition = Transmition.objects.get(pk=self.kwargs['transmition_id'])

        form.instance.author = self.request.user
        form.instance.transmition = transmition

        return super().form_valid(form)

    def get_success_url(self):
        return reverse('comments_transmition', kwargs={'transmition_id': self.object.transmition.id})

class CommentClassBase(LoginRequiredMixin):
    model = Comment

class MixinCommentAuthor:
    def get_object(self, queryset=None):
        course_id = self.kwargs.get('transmition_id')
        comment_id = self.kwargs.get('comment_id')
        return get_object_or_404(Comment, id=comment_id, transmition=course_id, author=self.request.user)

    def get_success_url(self):
        return reverse('comments_transmition', kwargs={'transmition_id': self.object.transmition.id})

class UpdateCommentView(MixinCommentAuthor, CommentClassBase, UpdateView):
    form_class = CommentForm
    template_name = 'update_comment.html'
    
class DeleteCommentView(MixinCommentAuthor, CommentClassBase, DeleteView):
    template_name = 'delete_comment.html'
"""