from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from .models import (
    Course, CategoryCourse, TagCourse, Portfolio, TagPortfolio,
    Subject, Link,
)
from django.urls import reverse
from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile
import os
from django.conf import settings

User = get_user_model()


class ModelTestCase(TestCase):

    def setUp(self):
        # User
        self.user = User.objects.create_user(
            username='testuser', password='12345', email='test@example.com'
        )

        # Portfolio and Tag
        self.tag_portfolio = TagPortfolio.objects.create(name='Django')
        self.portfolio = Portfolio.objects.create(
            user=self.user,
            title='My Projects'
        )
        self.portfolio.tags.add(self.tag_portfolio)

    # --- TESTS ---
    def test_user_created(self):
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(self.user.email, 'test@example.com')

    def test_portfolio_tag(self):
        self.assertIn(self.tag_portfolio, self.portfolio.tags.all())

@override_settings(TEMPLATES=[{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [os.path.join(settings.BASE_DIR, 'templates')],
    'APP_DIRS': True,
}])

class PortfolioViewsTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_login(self.user)

        # Tworzymy tagi testowe
        self.tag1 = TagPortfolio.objects.create(name='Python')
        self.tag2 = TagPortfolio.objects.create(name='Django')

        # Portfolio z jednym tagiem
        self.portfolio = Portfolio.objects.create(user=self.user, title='Initial Title')
        self.portfolio.tags.add(self.tag1)

    # GET - dodawanie portfolio
    def test_add_portfolio_view_get(self):
        url = reverse('add_portfolio')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'add_portfolio.html')

    # POST - dodawanie portfolio z istniejącym i nowymi tagami
    def test_add_portfolio_view_post(self):
        url = reverse('add_portfolio')
        post_data = {
            'title': 'My Portfolio Project',
            'tags_select': [self.tag1.id],  # wybór istniejącego taga
            'tags_input': 'NewTag1, NewTag2'  # nowe tagi do utworzenia
        }
        response = self.client.post(url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)

        portfolio = Portfolio.objects.filter(user=self.user, title='My Portfolio Project').first()
        self.assertIsNotNone(portfolio)

        # Sprawdzenie, że tagi zawierają wszystkie oczekiwane wartości
        tags_names = set(portfolio.tags.values_list('name', flat=True))
        self.assertSetEqual(tags_names, {'Python', 'NewTag1', 'NewTag2'})
        self.assertEqual(portfolio.tags.count(), 3)

    # GET - aktualizacja portfolio
    def test_update_portfolio_view_get(self):
        url = reverse('update_portfolio', kwargs={'portfolio_id': self.portfolio.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'update_portfolio.html')
        self.assertContains(response, 'Initial Title')

    # POST - aktualizacja portfolio: zmiana tytułu i tagów
    def test_update_portfolio_view_post(self):
        url = reverse('update_portfolio', kwargs={'portfolio_id': self.portfolio.id})
        post_data = {
            'title': 'Updated Title',
            'tags_select': [self.tag2.id],  # zmiana tagu
            'tags_input': 'NewTag3'         # dodanie nowego tagu
        }
        response = self.client.post(url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)

        self.portfolio.refresh_from_db()
        self.assertEqual(self.portfolio.title, 'Updated Title')

        # Sprawdzenie, że tagi są dokładnie takie, jak oczekiwane
        tags_names = set(self.portfolio.tags.values_list('name', flat=True))
        self.assertSetEqual(tags_names, {'Django', 'NewTag3'})
        self.assertNotIn('Python', tags_names)

    # GET - lista portfolio użytkownika z istniejącymi portfolio
    def test_portfolio_to_user_view_with_portfolios(self):
        # Tworzymy dodatkowe portfolio, aby lista była większa
        portfolio2 = Portfolio.objects.create(user=self.user, title='Sample Project')
        url = reverse('portfolio_to_user_view')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'portfolio_user_list.html')
        self.assertIn(self.portfolio, response.context['products'])
        self.assertIn(portfolio2, response.context['products'])

    # GET - lista portfolio użytkownika, gdy nie ma żadnego portfolio
    def test_portfolio_to_user_view_no_portfolios(self):
        Portfolio.objects.filter(user=self.user).delete()
        url = reverse('portfolio_to_user_view')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'portfolio_user_list.html')
        self.assertEqual(len(response.context['products']), 0)

class LinkViewsTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_login(self.user)

        self.portfolio = Portfolio.objects.create(user=self.user, title='Test Portfolio')

    def test_add_link_view_get(self):
        url = reverse('add_link', kwargs={'portfolio_id': self.portfolio.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'add_link.html')
        self.assertIn('formset', response.context)

    def test_add_link_view_post_valid(self):
        url = reverse('add_link', kwargs={'portfolio_id': self.portfolio.id})
        post_data = {
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-url': 'https://example.com',
        }
        response = self.client.post(url, data=post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Link.objects.filter(url='https://example.com', portfolio=self.portfolio).exists())

    def test_add_link_view_post_invalid(self):
        url = reverse('add_link', kwargs={'portfolio_id': self.portfolio.id})
        post_data = {
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-url': 'not-a-valid-url',
        }
        response = self.client.post(url, data=post_data)
        self.assertEqual(response.status_code, 200)  # Formularz renderowany ponownie
        self.assertFormsetError(response, 'formset', 0, 'url', 'Enter a valid URL.')

    def test_update_link_view_get(self):
        link = Link.objects.create(portfolio=self.portfolio, url='https://old-url.com')
        url = reverse('update_link', kwargs={'portfolio_id': self.portfolio.id, 'link_id': link.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'update_link.html')
        self.assertContains(response, 'https://old-url.com')

    def test_update_link_view_post(self):
        link = Link.objects.create(portfolio=self.portfolio, url='https://old-url.com')
        url = reverse('update_link', kwargs={'portfolio_id': self.portfolio.id, 'link_id': link.id})
        post_data = {
            'url': 'https://new-url.com',
        }
        response = self.client.post(url, data=post_data, follow=True)
        self.assertEqual(response.status_code, 200)

        link.refresh_from_db()
        self.assertEqual(link.url, 'https://new-url.com')