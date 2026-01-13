from django.http import HttpResponse
from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from .models import (
    Business, TagBusiness, CategoryEmploy, OffersJob,
    Course, CategoryCourse, TagCourse,
    CV, Experience, Portfolio, TagPortfolio,
    Subject, OffersJobUser, Link,
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

        # Business and Tag
        self.business = Business.objects.create(name='Test Company')
        self.tag = TagBusiness.objects.create(name='IT')
        self.business.tags.add(self.tag)

        # HR

        # Job Category and Offer
        self.category_employ = CategoryEmploy.objects.create(name='Engineering')
        self.offer = OffersJob.objects.create(
            title='Backend Developer',
            business=self.business,
            category=self.category_employ,
            file=SimpleUploadedFile('job.pdf', b'Test content')
        )
        self.offer.tags.add(self.tag)

        # Course, Tag, Subject, Test, Questions, Answers, Score
        self.cat_course = CategoryCourse.objects.create(name='Programming')
        self.tag_course = TagCourse.objects.create(name='Python')
        self.course = Course.objects.create(
            title='Intro to Python',
            author=self.user,
            category=self.cat_course
        )
        self.course.tags.add(self.tag_course)
        self.subject = Subject.objects.create(
            title='Python Basics',
            description='Intro lesson',
            file=SimpleUploadedFile('subject.pdf', b'Test content'),
            course=self.course
        )

        # CV and Experience
        self.cv = CV.objects.create(
            user=self.user,
            title='Senior Developer CV',
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            number_phone='123456789'
        )
        self.experience = Experience.objects.create(
            cv=self.cv,
            company='TechCorp',
            position='Developer'
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

    def test_business_tag(self):
        self.assertIn(self.tag, self.business.tags.all())

    def test_offer_creation(self):
        self.assertEqual(self.offer.title, 'Backend Developer')
        self.assertIn(self.tag, self.offer.tags.all())

    def test_course_and_subject(self):
        self.assertEqual(self.subject.course.title, 'Intro to Python')
        self.assertEqual(str(self.subject), 'Python Basics')

    def test_cv_and_experience(self):
        self.assertEqual(self.cv.title, 'Senior Developer CV')
        self.assertEqual(self.experience.cv, self.cv)

    def test_portfolio_tag(self):
        self.assertIn(self.tag_portfolio, self.portfolio.tags.all())

class OffersJobUserViewsTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.client.force_login(self.user)  # stabilniejsze logowanie

        self.business = Business.objects.create(name='Test Business')
        self.category = CategoryEmploy.objects.create(name='IT')

        self.offer = OffersJob.objects.create(
            title='Backend Developer',
            business=self.business,
            category=self.category,
            file=SimpleUploadedFile('testfile.pdf', b'file_content', content_type='application/pdf'),
        )

        self.offer_user = OffersJobUser.objects.create(
            offer=self.offer,
            user=self.user,
            is_accept=False
        )

    def test_add_offer_jobs_user_view_creates_entry(self):
        # Usuń istniejący wpis dla jednoznaczności testu
        OffersJobUser.objects.filter(offer=self.offer, user=self.user).delete()

        url = reverse('add_offer_jobs_user', kwargs={'offers_job_id': self.offer.id})
        response = self.client.post(url, {'user': self.user.id}, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(OffersJobUser.objects.filter(offer=self.offer, user=self.user).exists())

    def test_update_offer_jobs_user_view_get_renders_template(self):
        url = reverse('update_offer_jobs_user', kwargs={'offers_job_id': self.offer.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'update_offer_jobs_user.html')

    def test_update_offer_jobs_user_view_post_updates_accept(self):
        url = reverse('update_offer_jobs_user', kwargs={'offers_job_id': self.offer.id})
        response = self.client.post(url, {'is_accept': True})

        self.assertEqual(response.status_code, 302)  # przekierowanie po sukcesie
        self.offer_user.refresh_from_db()
        self.assertTrue(self.offer_user.is_accept)

    def test_accepted_offers_job_user_view_shows_accepted_offer(self):
        # Zaznacz ofertę jako zaakceptowaną
        self.offer_user.is_accept = True
        self.offer_user.save()

        url = reverse('index')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accepted_offers_job_user.html')
        self.assertIn(self.offer_user, response.context['products'])

    def test_accepted_offers_job_user_view_no_accepted_offers(self):
        # Nie ma zaakceptowanych ofert
        url = reverse('index')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        products = response.context['products']
        self.assertEqual(len(products), 0)

class DeleteOffersJobsViewTest(TestCase):
    def setUp(self):
        self.client = Client()

        # Użytkownicy
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.other_user = User.objects.create_user(username='otheruser', password='pass')

        # Logowanie
        self.client.force_login(self.user)  # stabilniejsze logowanie

        # Biznes i HR przypisany do użytkownika
        self.business = Business.objects.create(name="BiznesTest")

        # Kategoria wymagana przez OffersJob
        self.category = CategoryEmploy.objects.create(name="KategoriaTest")

        # Testowy plik dla pola file
        self.test_file = SimpleUploadedFile("testfile.txt", b"Test content")

        # Oferta utworzona przez zalogowanego użytkownika
        self.offer = OffersJob.objects.create(
            title="Oferta Testowa",
            business=self.business,
            category=self.category,
            file=self.test_file
        )

    def test_delete_own_offer_success(self):
        url = reverse('delete_offer_jobs', kwargs={'offer_jobs_id': self.offer.id})
        response = self.client.post(url)
        self.assertRedirects(response, reverse('offers_job_created_by_user'))
        self.assertFalse(OffersJob.objects.filter(id=self.offer.id).exists())

    def test_delete_foreign_offer_forbidden(self):
        # HR innego użytkownika, ale przypisany do tego samego biznesu

        foreign_offer = OffersJob.objects.create(
            title="Cudza Oferta",
            business=self.business,
            category=self.category,
            file=self.test_file
        )

        url = reverse('delete_offer_jobs', kwargs={'offer_jobs_id': foreign_offer.id})
        response = self.client.post(url)
        self.assertRedirects(response, reverse('offers_job_created_by_user'))
        self.assertTrue(OffersJob.objects.filter(id=foreign_offer.id).exists())

    def test_template_missing_returns_message(self):
        with override_settings(TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [],
            'APP_DIRS': False,
        }]):
            url = reverse('delete_offer_jobs', kwargs={'offer_jobs_id': self.offer.id})
            response = self.client.get(url)
            self.assertContains(response, "Brak pliku .html", status_code=200)

    def test_offers_created_by_user_view_displays_offers(self):
        url = reverse('offers_job_created_by_user')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.offer.title)

    def test_offers_created_by_user_template_missing_returns_404(self):
        with override_settings(TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [],
            'APP_DIRS': False,
        }]):
            url = reverse('offers_job_created_by_user')
            response = self.client.get(url)
            self.assertEqual(response.status_code, 404)
            self.assertContains(response, "Template not found", status_code=404)

@override_settings(TEMPLATES=[{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [os.path.join(settings.BASE_DIR, 'templates')],
    'APP_DIRS': True,
}])
class AddCourseIntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.client.force_login(self.user)  # ✅ stabilne logowanie

        # Kategoria potrzebna dla pola category
        self.category = CategoryCourse.objects.create(name="Kategoria Testowa")

    def test_full_course_creation_flow(self):
        add_course_url = reverse('add_course')
        course_data = {
            'title': 'Testowy kurs',
            'category': self.category.id,  # wymagane pole
            'tags_select': [],
            'tags_input': ''
        }

        response = self.client.post(add_course_url, course_data, follow=True)
        self.assertEqual(response.status_code, 200)

        # Sprawdzamy, czy kurs został utworzony
        course = Course.objects.first()
        self.assertIsNotNone(course)
        self.assertEqual(course.title, 'Testowy kurs')
        self.assertEqual(course.category, self.category)

class AddTestIntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.client.force_login(self.user)  # ✅ bardziej niezawodne niż login()

        # Tworzymy kategorię kursu i kurs
        self.category = CategoryCourse.objects.create(name="Kategoria Testowa")
        self.course = Course.objects.create(
            title="Kurs Testowy",
            category=self.category,
            author=self.user
        )

        # Tworzymy przedmiot (subject)
        self.subject = Subject.objects.create(
            title="Przedmiot Testowy",
            course=self.course
        )

class BusinessIntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.client.force_login(self.user)  # ✅ bardziej niezawodne niż login()

        # Tworzymy Business i HR powiązany z użytkownikiem
        self.business = Business.objects.create(name="Biznes Testowy")

    def test_update_business_view_get_and_post(self):
        url = reverse('update_business', kwargs={'business_id': self.business.id})

        # GET: wyświetlenie formularza
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Biznes Testowy')

        # POST: aktualizacja nazwy biznesu
        post_data = {'name': 'Biznes Zaktualizowany'}
        response = self.client.post(url, post_data, follow=True)

        # Sprawdzenie przekierowania
        self.assertRedirects(response, reverse('hr_to_business_view', kwargs={'business_id': self.business.id}))

        # Sprawdzenie aktualizacji w bazie danych
        self.business.refresh_from_db()
        self.assertEqual(self.business.name, 'Biznes Zaktualizowany')

    def test_hr_to_business_view(self):
        url = reverse('hr_to_business_view', kwargs={'business_id': self.business.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.username)

class OffersJobUserViewsTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_login(self.user)

        self.business = Business.objects.create(name='Test Business')

        self.category = CategoryEmploy.objects.create(name='IT')

        self.offer = OffersJob.objects.create(
            title='Backend Developer',
            business=self.business,
            category=self.category,
            file=SimpleUploadedFile('testfile.pdf', b'file_content', content_type='application/pdf'),
        )

        self.offer_user = OffersJobUser.objects.create(
            offer=self.offer,
            user=self.user,
            is_accept=False
        )

    def test_add_offer_jobs_user_view(self):
        OffersJobUser.objects.filter(offer=self.offer, user=self.user).delete()

        url = reverse('add_offer_jobs_user', kwargs={'offers_job_id': self.offer.id})
        response = self.client.post(url, {'user': self.user.id}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(OffersJobUser.objects.filter(offer=self.offer, user=self.user).exists())

    def test_update_offer_jobs_user_view_get(self):
        url = reverse('update_offer_jobs_user', kwargs={'offers_job_id': self.offer.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'update_offer_jobs_user.html')

    def test_update_offer_jobs_user_view_post(self):
        url = reverse('update_offer_jobs_user', kwargs={'offers_job_id': self.offer.id})
        response = self.client.post(url, {'is_accept': True}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.offer_user.refresh_from_db()
        self.assertTrue(self.offer_user.is_accept)

    def test_accepted_offers_job_user_view(self):
        self.offer_user.is_accept = True
        self.offer_user.save()

        url = reverse('index')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accepted_offers_job_user.html')
        self.assertIn('products', response.context)
        self.assertIn(self.offer_user, response.context['products'])

    def test_accepted_offers_job_user_view_no_accepted_offers(self):
        url = reverse('index')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('products', response.context)
        self.assertEqual(len(response.context['products']), 0)

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

class AddExperienceViewTest(TestCase):

    def setUp(self):
        # Tworzymy testowego użytkownika i CV
        self.user = User.objects.create_user(username='testuser', password='pass12345')
        self.client = Client()
        self.client.force_login(self.user)

        self.cv = CV.objects.create(
            user=self.user,
            title='Test CV',
            first_name='Jan',
            last_name='Kowalski',
            email='jan@example.com',
            number_phone='123456789'
        )
        self.url = reverse('add_experience', kwargs={'cv_id': self.cv.id})

    def test_add_experience_post_valid(self):
        post_data = {
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-company': 'Example Company',
            'form-0-position': 'Developer',
            'form-0-DELETE': '',  # nie usuwamy formularza
        }

        response = self.client.post(self.url, data=post_data, follow=True)
        self.assertEqual(response.status_code, 200)  # follow=True śledzi redirect

        # Sprawdzamy, czy dane się zapisały w bazie
        self.assertTrue(Experience.objects.filter(cv=self.cv, company='Example Company', position='Developer').exists())

    def test_add_experience_post_invalid(self):
        post_data = {
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-company': '',
            'form-0-position': 'Developer',
            'form-0-DELETE': '',
        }

        response = self.client.post(self.url, data=post_data)
        # Formularz niepoprawny – render ponownie
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Experience.objects.filter(cv=self.cv, position='Developer').exists())

    def test_update_experience_view_post_valid(self):
        experience = Experience.objects.create(cv=self.cv, company='Old Company', position='Tester')
        url = reverse('update_experience', kwargs={'cv_id': self.cv.id, 'experience_id': experience.id})

        post_data = {
            'company': 'New Company',
            'position': 'Senior Tester',
        }

        response = self.client.post(url, data=post_data, follow=True)
        self.assertEqual(response.status_code, 200)  # follow=True śledzi redirect

        experience.refresh_from_db()
        self.assertEqual(experience.company, 'New Company')
        self.assertEqual(experience.position, 'Senior Tester')

    def test_my_cv_experience_view(self):
        Experience.objects.create(cv=self.cv, company='Company1', position='Position1')
        Experience.objects.create(cv=self.cv, company='Company2', position='Position2')

        url = reverse('my_cv_experience_view')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Company1')
        self.assertContains(response, 'Company2')


class CVViewsTest(TestCase):

    def setUp(self):
        # Utwórz użytkownika i zaloguj
        self.user = User.objects.create_user(username='testuser', password='test12345')
        self.client = Client()
        self.client.force_login(self.user)

        # Przygotuj dane do CV
        self.cv_data = {
            'title': 'My CV',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'number_phone': '123456789',
        }

    def test_add_cv_view_get(self):
        url = reverse('add_cv')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'add_cv.html')
        self.assertIn('form', response.context)

    def test_add_cv_view_post_valid(self):
        url = reverse('add_cv')
        response = self.client.post(url, data=self.cv_data, follow=True)

        # Sprawdź, czy CV zostało faktycznie utworzone
        self.assertEqual(CV.objects.count(), 1)
        cv = CV.objects.get(user=self.user)

        # Sprawdź przekierowanie na add_experience/<cv.id>
        self.assertRedirects(response, reverse('add_experience', args=[cv.id]))

        # Dodatkowe asercje
        self.assertEqual(cv.title, self.cv_data['title'])
        self.assertEqual(cv.user, self.user)

    def test_update_cv_view_get(self):
        cv = CV.objects.create(user=self.user, **self.cv_data)
        url = reverse('update_cv', kwargs={'cv_id': cv.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'update_cv.html')
        self.assertIn('form', response.context)

    def test_update_cv_view_post_valid(self):
        cv = CV.objects.create(user=self.user, **self.cv_data)
        url = reverse('update_cv', kwargs={'cv_id': cv.id})

        updated_data = {
            'title': 'Updated CV',
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'jane.doe@example.com',
            'number_phone': '987654321',
        }
        response = self.client.post(url, data=updated_data, follow=True)
        self.assertRedirects(response, reverse('cv_to_user_view'))

        cv.refresh_from_db()
        self.assertEqual(cv.title, 'Updated CV')
        self.assertEqual(cv.first_name, 'Jane')
        self.assertEqual(cv.email, 'jane.doe@example.com')

    def test_dispatch_returns_message_if_template_missing(self):
        url_add = reverse('add_cv')
        with patch('workapp.views.check_template', return_value=False):
            response = self.client.get(url_add)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "Brak pliku .html")

        cv = CV.objects.create(user=self.user, **self.cv_data)
        url_update = reverse('update_cv', kwargs={'cv_id': cv.id})
        with patch('workapp.views.check_template', return_value=False):
            response = self.client.get(url_update)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "Brak pliku .html")
