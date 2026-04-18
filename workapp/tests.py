# tests/test_views.py
from django.test import TestCase, Client
from django.urls import reverse
from .models import TagPortfolio, Link
from .forms import LinkForm
from django.contrib.auth.models import User

class LinkFormTest(TestCase):
    def test_valid_form(self):
        tag = TagPortfolio.objects.create(name="TestTag")
        data = {'description': 'Poprawny opis w języku polskim', 'tags': str(tag.id)}
        form = LinkForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_form_empty_description(self):
        tag = TagPortfolio.objects.create(name="TestTag")
        data = {'description': '', 'tags': str(tag.id)}
        form = LinkForm(data=data)
        self.assertFalse(form.is_valid())

class AddLinkViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('add_link')
        self.tag = TagPortfolio.objects.create(name="TestTag")
        self.user = User.objects.create_user(username='testuser', password='12345')

    def test_get_add_link_view(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'add_link.html')

    def test_post_add_link_view_valid(self):
        data = {'description': 'Poprawny opis w języku polskim', 'tags': str(self.tag.id)}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('thanks'))
        self.assertEqual(Link.objects.count(), 1)

    def test_post_add_link_view_invalid(self):
        data = {'description': '', 'tags': str(self.tag.id)}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        # Sprawdzamy komunikat błędu w formularzu
        self.assertEqual(response.context['form'].errors['description'], ['To pole jest wymagane'])

class SearchPortfolioViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('search_portfolio')
        self.tag1 = TagPortfolio.objects.create(name="Tag1")
        self.tag2 = TagPortfolio.objects.create(name="Tag2")

        # Tworzymy linki z poprawnym opisem i pojedynczym tagiem
        Link.objects.create(description="Poprawny opis pierwszy", tags=self.tag1)
        Link.objects.create(description="Poprawny opis drugi", tags=self.tag2)
        Link.objects.create(description="123456", tags=self.tag1)  # niepoprawny wg is_valid_text

    def test_search_portfolio_no_filter(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('portfolios', response.context)
        self.assertEqual(len(response.context['portfolios']), 2)

    def test_search_portfolio_with_tag_filter(self):
        link = Link.objects.create(description="Test z tagiem", tags=self.tag1)
        response = self.client.get(self.url, {'tags': str(self.tag1.id)})
        self.assertEqual(response.status_code, 200)
        portfolios = response.context['portfolios']
        self.assertTrue(all(self.tag1 == p.tags for p in portfolios))

    def test_search_portfolio_pagination(self):
        # Dodajemy 25 linków z poprawnymi opisami
        for i in range(25):
            Link.objects.create(
                description=f"Poprawny opis {i}",
                is_valid=True
            )

        response = self.client.get(self.url)

        page_obj = response.context['page_obj']

        # 25 elementów przy paginate_by=20 => 2 strony
        self.assertEqual(page_obj.paginator.num_pages, 2)

        # Na pierwszej stronie powinno być 20 elementów
        self.assertEqual(len(page_obj.object_list), 20)

class ThankingViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('thanks')

    def test_thanking_view(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'thanks.html')