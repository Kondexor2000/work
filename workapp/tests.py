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

        # Portfolio and Tag
        self.tag_portfolio = TagPortfolio.objects.create(name='Django')
        self.portfolio = Link.objects.create(
            description='My Projects'
        )
        self.portfolio.tags.add(self.tag_portfolio)

    def test_portfolio_tag(self):
        self.assertIn(self.tag_portfolio, self.portfolio.tags.all())

class LinkViewsTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.portfolio = TagPortfolio.objects.create(name='Test Portfolio')

    def test_add_link_view_get(self):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'add_link.html')
        self.assertIn('formset', response.context)

    def test_add_link_view_post_valid(self):
        post_data = {
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-url': 'https://example.com',
        }
        response = self.client.post(url, data=post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Link.objects.filter(tags=self.portfolio).exists())

    def test_add_link_view_post_invalid(self):
        url = reverse('add_link')
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