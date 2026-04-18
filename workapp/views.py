from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.db import transaction
from django.db.models import Q
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, TemplateView
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
from .forms import LinkForm

logger = logging.getLogger(__name__)

# === Link ===

class AddLinkView(CreateView):
    form_class = LinkForm
    template_name = 'add_link.html'
    
    def get_success_url(self):
        logger.info(
            "NEW LINK CREATED: id=%s, description=%s",
            self.object.id,
            self.object.description
        )
        return reverse('thanks')

class SearchPortfolioView(ListView):
    model = Link
    template_name = 'search_portfolio.html'
    context_object_name = 'portfolios'
    paginate_by = 20

    def get_queryset(self):
        queryset = (
            Link.objects
            .filter(is_valid=True)
            .prefetch_related('tags')
            .order_by('description')
        )

        logger.info(queryset.values('id', 'description'))

        tags_id = self.request.GET.get('tags')

        if tags_id and tags_id.isdigit():
            queryset = queryset.filter(tags__id=int(tags_id)).order_by('description')
            logger.info(queryset.values('id', 'description'))

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tags'] = TagPortfolio.objects.all()
        return context

class ThankingView(TemplateView):
    template_name = 'thanks.html'