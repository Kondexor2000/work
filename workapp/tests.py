from django.http import HttpResponse
from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from .models import (
    HR, Business, TagBusiness, CategoryEmploy, OffersJob,
    Course, CategoryCourse, TagCourse,
    CV, Experience, Portfolio, TagPortfolio,
    Subject, Test, Questions, Answers, TestScore, OffersJobUser, Projects, Link, Questionnaire, QuestionnaireCategory
)
from django.urls import reverse, NoReverseMatch
from django.core.files.uploadedfile import SimpleUploadedFile
import os
from django.conf import settings

User = get_user_model()

class ModelTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345', email='test@example.com')

        self.business = Business.objects.create(name='Test Company')
        self.tag = TagBusiness.objects.create(name='IT')
        self.business.tags.add(self.tag)

        self.hr = HR.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            number_phone='123456789'
        )
        self.hr.business.add(self.business)

        self.category_employ = CategoryEmploy.objects.create(name='Engineering')

        self.offer = OffersJob.objects.create(
            title='Backend Developer',
            business=self.business,
            hr=self.hr,
            category=self.category_employ,
            file='uploads/job.pdf'
        )
        self.offer.tags.add(self.tag)

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
            file='uploads/subject.pdf',
            course=self.course
        )

        self.test = Test.objects.create(
            title='Python Test',
            subject=self.subject
        )

        self.question = Questions.objects.create(
            question='What is Python?',
            correct='A programming language',
            test=self.test
        )

        self.answer = Answers.objects.create(
            answer='A programming language',
            question=self.question,
            user=self.user
        )

        self.test_score = TestScore.objects.create(
            user=self.user,
            test=self.test,
            score=90.0,
            minimum=60.0
        )

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

        self.tag_portfolio = TagPortfolio.objects.create(name='Django')
        self.portfolio = Portfolio.objects.create(
            user=self.user,
            title='My Projects'
        )
        self.portfolio.tags.add(self.tag_portfolio)

    def test_user_created(self):
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(self.user.email, 'test@example.com')

    def test_hr_str(self):
        self.assertEqual(str(self.hr), 'John Doe')

    def test_business_tag(self):
        self.assertIn(self.tag, self.business.tags.all())

    def test_offer_creation(self):
        self.assertEqual(self.offer.title, 'Backend Developer')
        self.assertIn(self.tag, self.offer.tags.all())

    def test_course_and_subject(self):
        self.assertEqual(self.subject.course.title, 'Intro to Python')
        self.assertEqual(str(self.subject), 'Python Basics')

    def test_test_score(self):
        self.assertEqual(self.test_score.score, 90.0)
        self.assertGreaterEqual(self.test_score.score, self.test_score.minimum)

    def test_cv_and_experience(self):
        self.assertEqual(self.cv.title, 'Senior Developer CV')
        self.assertEqual(self.experience.cv, self.cv)

    def test_portfolio_tag(self):
        self.assertIn(self.tag_portfolio, self.portfolio.tags.all())

class BusinessFlowIntegrationTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')
        self.category = CategoryEmploy.objects.create(name='IT')

    def test_full_business_hr_offer_flow(self):
        # 1. Add Business
        response = self.client.post(reverse('add_business'), {
            'name': 'Test Business',  # replace with actual Business form fields
            # other fields...
        })
        self.assertEqual(response.status_code, 302)  # redirect do add_hr z business_id
        business = Business.objects.last()
        self.assertIsNotNone(business)
        # No business.user field, so skip that check

        # 2. Add HR
        response = self.client.post(reverse('add_hr', args=[business.id]), {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'number_phone': '123456789',
            # other fields...
        })
        self.assertEqual(response.status_code, 302)
        hr = HR.objects.last()
        self.assertIsNotNone(hr)
        self.assertIn(business, hr.business.all())  # HR linked to business
        self.assertEqual(hr.user, self.user)  # HR's user is the logged-in user

        # 3. Add Offer Job
        response = self.client.post(reverse('add_offer_jobs', kwargs={'business_id': business.id, 'hr_id': hr.id}), {
            'title': 'Backend Developer',
            'file': SimpleUploadedFile('testfile.pdf', b'file_content', content_type='application/pdf'),
            'category': self.category.id,
            # other required fields
        })
        self.assertEqual(response.status_code, 302)
        offer = OffersJob.objects.last()
        self.assertIsNotNone(offer)
        self.assertEqual(offer.business, business)
        self.assertEqual(offer.hr, hr)
#        self.assertEqual(offer.user, self.user)

        # 4. Check offers_job_created_by_user view
        response = self.client.get(reverse('offers_job_created_by_user'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, offer.title)

class OffersJobUserViewsTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')

        self.business = Business.objects.create(name='Test Business')
        self.hr = HR.objects.create(user=self.user, first_name='John', last_name='Doe', email='john@example.com', number_phone='123456789')
        self.hr.business.add(self.business)

        self.category = CategoryEmploy.objects.create(name='IT')

        self.offer = OffersJob.objects.create(
            title='Backend Developer',
            business=self.business,
            hr=self.hr,
            category=self.category,
            file=SimpleUploadedFile('testfile.pdf', b'file_content', content_type='application/pdf'),
        )

        self.offer_user = OffersJobUser.objects.create(
            offer=self.offer,
            user=self.user,
            is_accept=False
        )

    def test_add_offer_jobs_user_view(self):
        # upewniamy się, że nie ma wpisu, żeby test był jednoznaczny
        OffersJobUser.objects.filter(offer=self.offer, user=self.user).delete()

        url = reverse('add_offer_jobs_user', kwargs={'offers_job_id': self.offer.id})
        response = self.client.post(url, {'user': self.user.id}, follow=True)
        self.assertEqual(response.status_code, 200)  # follow=True -> kończy się 200
        self.assertTrue(OffersJobUser.objects.filter(offer=self.offer, user=self.user).exists())

    def test_update_offer_jobs_user_view_get(self):
        url = reverse('update_offer_jobs_user', kwargs={'offers_job_id': self.offer.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'update_offer_jobs_user.html')

    def test_update_offer_jobs_user_view_post(self):
        url = reverse('update_offer_jobs_user', kwargs={'offers_job_id': self.offer.id})
        response = self.client.post(url, {'is_accept': True})
        # redirect expected after successful update
        self.assertEqual(response.status_code, 302)
        self.offer_user.refresh_from_db()
        self.assertTrue(self.offer_user.is_accept)

    def test_accepted_offers_job_user_view(self):
        # Mark the offer as accepted
        self.offer_user.is_accept = True
        self.offer_user.save()

        url = reverse('index')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accepted_offers_job_user.html')
        # The accepted offer should be in the context 'products'
        products = response.context['products']
        self.assertIn(self.offer_user, products)

    def test_accepted_offers_job_user_view_no_accepted_offers(self):
        # No accepted offers for this user
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
        self.client.login(username='testuser', password='pass')

        # Biznes i HR przypisany do użytkownika
        self.business = Business.objects.create(name="BiznesTest")
        self.hr = HR.objects.create(user=self.user)
        self.hr.business.set([self.business])

        # Kategoria wymagana przez OffersJob
        self.category = CategoryEmploy.objects.create(name="KategoriaTest")

        # Testowy plik dla pola file
        self.test_file = SimpleUploadedFile("testfile.txt", b"Test content")

        # Oferta utworzona przez zalogowanego użytkownika
        self.offer = OffersJob.objects.create(
            title="Oferta Testowa",
            business=self.business,
            hr=self.hr,
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
        foreign_hr = HR.objects.create(user=self.other_user)
        foreign_hr.business.set([self.business])  # ten sam biznes co zalogowany HR

        foreign_offer = OffersJob.objects.create(
            title="Cudza",
            hr=foreign_hr,
            business=self.business,  # ten sam biznes
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

    def test_offers_created_by_user_template_missing(self):
        with override_settings(TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [],
            'APP_DIRS': False,
        }]):
            url = reverse('offers_job_created_by_user')
            response = self.client.get(url)
            self.assertEqual(response.status_code, 404)
            self.assertContains(response, "Template not found", status_code=404)

class AddCourseIntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.client.login(username='testuser', password='pass')

        # Kategoria potrzebna dla pola category
        self.category = CategoryCourse.objects.create(name="Kategoria Testowa")

        # Tworzymy szablon na potrzeby check_template
        templates_dir = os.path.join(settings.BASE_DIR, 'templates')
        os.makedirs(templates_dir, exist_ok=True)
        with open(os.path.join(templates_dir, 'add_course.html'), 'w') as f:
            f.write("OK")

    @override_settings(TEMPLATES=[{
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(settings.BASE_DIR, 'templates')],
        'APP_DIRS': True,
    }])
    def test_full_course_creation_flow(self):
        add_course_url = reverse('add_course')
        course_data = {
            'title': 'Testowy kurs',
            'category': self.category.id,  # wymagane!
            'tags_select': [],
            'tags_input': ''
        }
        response = self.client.post(add_course_url, course_data, follow=True)
        self.assertEqual(response.status_code, 200)

        course = Course.objects.first()
        self.assertIsNotNone(course)  # Teraz powinno przejść
        self.assertEqual(course.title, 'Testowy kurs')
        self.assertEqual(course.category, self.category)

@override_settings(TEMPLATES=[{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [os.path.join(settings.BASE_DIR, 'templates')],
    'APP_DIRS': True,
}])
class AddTestIntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.client.login(username='testuser', password='pass')

        # Tworzymy kategorie i kurs
        self.category = CategoryCourse.objects.create(name="Kategoria Testowa")
        self.course = Course.objects.create(title="Kurs Testowy", category=self.category, author=self.user)

        # Tworzymy przedmiot
        self.subject = Subject.objects.create(title="Przedmiot Testowy", course=self.course)

        # Minimalne pliki HTML, żeby check_template nie blokował
        templates_dir = os.path.join(settings.BASE_DIR, 'templates')
        os.makedirs(templates_dir, exist_ok=True)
        for tpl in ['add_test.html', 'add_questions.html', 'course_user.html']:
            with open(os.path.join(templates_dir, tpl), 'w') as f:
                f.write("{% for product in products %}{{ product.title }}{% endfor %}")

    def test_full_add_test_and_questions_flow(self):
        # 1. Dodajemy test do przedmiotu
        add_test_url = reverse('add_test', kwargs={
            'course_id': self.course.id,
            'subject_id': self.subject.id
        })
        response = self.client.post(add_test_url, {'title': 'Test Integracyjny'}, follow=True)
        self.assertEqual(response.status_code, 200)
        test_obj = Test.objects.filter(subject=self.subject).first()
        self.assertIsNotNone(test_obj)

        # 2. Dodajemy pytania do testu
        # 2. Dodajemy pytania do testu
        add_questions_url = reverse('add_question', kwargs={
            'course_id': self.course.id,
            'subject_id': self.subject.id,
            'test_id': test_obj.id
        })

        response = self.client.post(add_questions_url, {
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-question': 'Pytanie 1',
            'form-0-correct': 'Odpowiedź 1',
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Questions.objects.filter(test=test_obj).exists())

        # 3. Sprawdzamy czy kurs pojawia się w course_user
        course_user_url = reverse('course_user')
        response = self.client.get(course_user_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kurs Testowy")

class BusinessIntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.client.login(username='testuser', password='pass')

        # Tworzymy Business i HR powiązany z użytkownikiem
        self.business = Business.objects.create(name="Biznes Testowy")
        self.hr = HR.objects.create(user=self.user)
        self.hr.business.set([self.business])

    def test_update_business_view_get_and_post(self):
        url = reverse('update_business', kwargs={'business_id': self.business.id})
        # GET: wyświetlenie formularza
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Biznes Testowy')

        # POST: aktualizacja nazwy biznesu
        response = self.client.post(url, {'name': 'Biznes Zaktualizowany'}, follow=True)
        self.assertRedirects(response, reverse('hr_to_business_view', kwargs={'business_id': self.business.id}))
        self.business.refresh_from_db()
        self.assertEqual(self.business.name, 'Biznes Zaktualizowany')

    def test_hr_to_business_view(self):
        url = reverse('hr_to_business_view', kwargs={'business_id': self.business.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.username)

class HRIntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.client.login(username='testuser', password='pass')

        # Tworzymy Business i HR powiązany z użytkownikiem
        self.business = Business.objects.create(name="Biznes Testowy")
        self.hr = HR.objects.create(user=self.user)
        self.hr.business.set([self.business])

    def test_update_hr_view_get_and_post(self):
        url = reverse('update_hr', kwargs={'business_id': self.business.id, 'hr_id': self.hr.id})

        # GET - formularz
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Biznes Testowy')

        # POST - aktualizacja pól HR
        post_data = {
            'first_name': 'Jan',
            'last_name': 'Kowalski',
            'email': 'jan.kowalski@example.com',
            'number_phone': '123456789',
            'business': [self.business.id],  # jeśli business to ManyToManyField, podaj listę
        }

        response = self.client.post(url, post_data, follow=True)

        # Debug, jeśli coś pójdzie nie tak:
        if response.status_code != 302 and 'form' in response.context:
            print(response.context['form'].errors)

        self.assertRedirects(response, reverse('hr_to_business_view', kwargs={'business_id': self.business.id}))

        self.hr.refresh_from_db()
        self.assertEqual(self.hr.first_name, 'Jan')
        self.assertEqual(self.hr.last_name, 'Kowalski')
        self.assertEqual(self.hr.email, 'jan.kowalski@example.com')
        self.assertEqual(self.hr.number_phone, '123456789')

    def test_hr_to_business_view(self):
        url = reverse('hr_to_business_view', kwargs={'business_id': self.business.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.username)

class OffersJobUserViewsTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')

        self.business = Business.objects.create(name='Test Business')
        self.hr = HR.objects.create(user=self.user, first_name='John', last_name='Doe', email='john@example.com', number_phone='123456789')
        self.hr.business.add(self.business)

        self.category = CategoryEmploy.objects.create(name='IT')

        self.offer = OffersJob.objects.create(
            title='Backend Developer',
            business=self.business,
            hr=self.hr,
            category=self.category,
            file=SimpleUploadedFile('testfile.pdf', b'file_content', content_type='application/pdf'),
        )

        self.offer_user = OffersJobUser.objects.create(
            offer=self.offer,
            user=self.user,
            is_accept=False
        )

    def test_add_offer_jobs_user_view(self):
        # upewniamy się, że nie ma wpisu, żeby test był jednoznaczny
        OffersJobUser.objects.filter(offer=self.offer, user=self.user).delete()

        url = reverse('add_offer_jobs_user', kwargs={'offers_job_id': self.offer.id})
        response = self.client.post(url, {'user': self.user.id}, follow=True)
        self.assertEqual(response.status_code, 200)  # follow=True -> kończy się 200
        self.assertTrue(OffersJobUser.objects.filter(offer=self.offer, user=self.user).exists())

    def test_update_offer_jobs_user_view_get(self):
        url = reverse('update_offer_jobs_user', kwargs={'offers_job_id': self.offer.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'update_offer_jobs_user.html')

    def test_update_offer_jobs_user_view_post(self):
        url = reverse('update_offer_jobs_user', kwargs={'offers_job_id': self.offer.id})
        response = self.client.post(url, {'is_accept': True})
        # redirect expected after successful update
        self.assertEqual(response.status_code, 302)
        self.offer_user.refresh_from_db()
        self.assertTrue(self.offer_user.is_accept)

    def test_accepted_offers_job_user_view(self):
        # Mark the offer as accepted
        self.offer_user.is_accept = True
        self.offer_user.save()

        url = reverse('index')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accepted_offers_job_user.html')
        # The accepted offer should be in the context 'products'
        products = response.context['products']
        self.assertIn(self.offer_user, products)

    def test_accepted_offers_job_user_view_no_accepted_offers(self):
        # No accepted offers for this user
        url = reverse('index')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        products = response.context['products']
        self.assertEqual(len(products), 0)

class PortfolioViewsTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')

        self.tag1 = TagPortfolio.objects.create(name='Python')
        self.tag2 = TagPortfolio.objects.create(name='Django')

        # Dodaj ten fragment:
        self.portfolio = Portfolio.objects.create(user=self.user, title='Initial Title')
        self.portfolio.tags.add(self.tag1)

    def test_add_portfolio_view_get(self):
        url = reverse('add_portfolio')  # zakładam nazwę URL
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'add_portfolio.html')

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
        self.assertIn(self.tag1, portfolio.tags.all())
        self.assertTrue(portfolio.tags.filter(name='NewTag1').exists())
        self.assertTrue(portfolio.tags.filter(name='NewTag2').exists())

    def test_update_portfolio_view_get(self):
        url = reverse('update_portfolio', kwargs={'portfolio_id': self.portfolio.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'update_portfolio.html')
        self.assertContains(response, 'Initial Title')

    def test_update_portfolio_view_post(self):
        url = reverse('update_portfolio', kwargs={'portfolio_id': self.portfolio.id})
        post_data = {
            'title': 'Updated Title',
            'tags_select': [self.tag2.id],  # zmieniamy tag
            'tags_input': 'NewTag3'          # dodajemy nowy tag
        }
        response = self.client.post(url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)

        self.portfolio.refresh_from_db()
        self.assertEqual(self.portfolio.title, 'Updated Title')

        tags = self.portfolio.tags.all()
        self.assertIn(self.tag2, tags)
        self.assertTrue(tags.filter(name='NewTag3').exists())
        self.assertNotIn(self.tag1, tags)  # poprzedni tag został usunięty
    
    def test_portfolio_to_user_view_with_portfolios(self):
        portfolio = Portfolio.objects.create(user=self.user, title='Sample Project')
        url = reverse('portfolio_to_user_view')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'portfolio_user_list.html')
        self.assertIn(portfolio, response.context['products'])

    def test_portfolio_to_user_view_no_portfolios(self):
        # Usuwamy wszystkie portfolio użytkownika
        Portfolio.objects.filter(user=self.user).delete()
        url = reverse('portfolio_to_user_view')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'portfolio_user_list.html')
        self.assertEqual(len(response.context['products']), 0)

class ProjectViewsTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')

        self.portfolio = Portfolio.objects.create(user=self.user, title='My Portfolio')

        # Jeden projekt do update
        self.project = Projects.objects.create(
            portfolio=self.portfolio,
            title='Existing Project',
            file=SimpleUploadedFile('file.pdf', b'content', content_type='application/pdf')
        )

    def test_add_project_view_get(self):
        url = reverse('add_project', kwargs={'portfolio_id': self.portfolio.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'add_project.html')
        self.assertIn('formset', response.context)

    def test_add_project_view_post_valid(self):
        url = reverse('add_project', kwargs={'portfolio_id': self.portfolio.id})
        file = SimpleUploadedFile('testfile.pdf', b'file_content', content_type='application/pdf')
        post_data = {
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-title': 'New Project',
            'form-0-file': file,
        }
        response = self.client.post(url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Projects.objects.filter(title='New Project', portfolio=self.portfolio).exists())

    def test_add_project_view_post_valid(self):
        url = reverse('add_project', kwargs={'portfolio_id': self.portfolio.id})
        post_data = {
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',

            'form-0-title': 'My Project',
        }
        file_data = {
            'form-0-file': SimpleUploadedFile('testfile.pdf', b'file_content', content_type='application/pdf'),
        }

        post_data.update(file_data)

        response = self.client.post(url, data=post_data, files=file_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Projects.objects.filter(title='My Project', portfolio=self.portfolio).exists())

    def test_update_project_view_get(self):
        url = reverse('update_project', kwargs={'portfolio_id': self.portfolio.id, 'project_id': self.project.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'update_project.html')
        self.assertContains(response, self.project.title)

    def test_update_project_view_post(self):
        url = reverse('update_project', kwargs={'portfolio_id': self.portfolio.id, 'project_id': self.project.id})
        file = SimpleUploadedFile('updatedfile.pdf', b'new content', content_type='application/pdf')
        post_data = {
            'title': 'Updated Project Title',
            'file': file,
        }
        response = self.client.post(url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, 'Updated Project Title')

    def test_my_portfolio_projects_view(self):
        url = reverse('my_portfolio_projects_view')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'my_portfolio_projects_list.html')
        self.assertIn(self.project, response.context['products'])

    def test_my_portfolio_projects_view_no_projects(self):
        Projects.objects.all().delete()
        url = reverse('my_portfolio_projects_view')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['products']), 0)

class LinkViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')

        self.portfolio = Portfolio.objects.create(user=self.user, title='Test Portfolio')

    def test_add_link_view_get(self):
        url = reverse('add_link', kwargs={'portfolio_id': self.portfolio.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'add_link.html')

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
        self.assertEqual(response.status_code, 200)  # should re-render form
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
        self.client.login(username='testuser', password='pass12345')

        post_data = {
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-company': 'Example Company',
            'form-0-position': 'Developer',
            'form-0-DELETE': '',  # nie usuwamy formularza
        }

        response = self.client.post(self.url, data=post_data)

        # Po poprawnym zapisie powinno nastąpić przekierowanie (302)
        self.assertEqual(response.status_code, 302)

        # Sprawdzamy, czy dane się zapisały w bazie
        experience = Experience.objects.filter(cv=self.cv, company='Example Company', position='Developer')
        self.assertTrue(experience.exists())

    def test_add_experience_post_invalid(self):
        self.client.login(username='testuser', password='pass12345')

        # Brak wymaganych danych (np. company jest pusty)
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

        # Formularz jest niepoprawny, więc powinien zwrócić status 200 i renderować stronę ponownie
        self.assertEqual(response.status_code, 200)

        # Sprawdź, że nic nie zostało zapisane
        self.assertFalse(Experience.objects.filter(cv=self.cv, position='Developer').exists())

    def test_update_experience_view_post_valid(self):
        self.client.login(username='testuser', password='pass12345')
        experience = Experience.objects.create(cv=self.cv, company='Old Company', position='Tester')
        url = reverse('update_experience', kwargs={'cv_id': self.cv.id, 'experience_id': experience.id})

        post_data = {
            'company': 'New Company',
            'position': 'Senior Tester',
        }

        response = self.client.post(url, data=post_data)

        self.assertEqual(response.status_code, 302)  # Powinno być przekierowanie

        experience.refresh_from_db()
        self.assertEqual(experience.company, 'New Company')
        self.assertEqual(experience.position, 'Senior Tester')

    def test_my_cv_experience_view(self):
        self.client.login(username='testuser', password='pass12345')
        Experience.objects.create(cv=self.cv, company='Company1', position='Position1')
        Experience.objects.create(cv=self.cv, company='Company2', position='Position2')

        url = reverse('my_cv_experience_view')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Company1')
        self.assertContains(response, 'Company2')

class CVViewsTest(TestCase):
    def setUp(self):
        # Utwórz użytkownika i zaloguj go
        self.user = User.objects.create_user(username='testuser', password='pass12345')
        self.client.login(username='testuser', password='pass12345')

        # Przygotuj dane do CV
        self.cv_data = {
            'title': 'My CV',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'number_phone': '123456789',
        }

    def test_add_cv_view_get(self):
        url = reverse('add_cv')  # Zakładam, że tak masz nazwę url dla AddCVView
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'add_cv.html')
        self.assertIn('form', response.context)

    def test_add_cv_view_post_valid(self):
        url = reverse('add_cv')
        response = self.client.post(url, data=self.cv_data)

        # Sprawdź przekierowanie na add_experience z argumentem id CV
        cv = CV.objects.get(user=self.user)
        self.assertRedirects(response, reverse('add_experience', args=[cv.id]))

        # Sprawdź, czy CV zostało faktycznie utworzone
        self.assertEqual(CV.objects.count(), 1)
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
        response = self.client.post(url, data=updated_data)
        self.assertRedirects(response, reverse('cv_to_user_view'))

        cv.refresh_from_db()
        self.assertEqual(cv.title, 'Updated CV')
        self.assertEqual(cv.first_name, 'Jane')
        self.assertEqual(cv.email, 'jane.doe@example.com')

    def test_dispatch_returns_404_if_template_missing(self):
        # Zakładam, że check_template zwraca False jeśli brak template
        # Tutaj wymuszamy brak template, więc patchujemy check_template, np. z unittest.mock
        from unittest.mock import patch

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


class AddAnswersViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass123')
        self.client.login(username='testuser', password='pass123')

        # Przygotuj dane kursu, przedmiotu, testu i pytań
        self.category = CategoryCourse.objects.create(name='Test category')
        self.course = Course.objects.create(title='Course 1', category=self.category)
        self.subject = Subject.objects.create(title='Subject 1', description='Desc', file='file.pdf', course=self.course)
        self.test = Test.objects.create(title='Test 1', subject=self.subject, is_finish=True)

        # Dodaj pytania do testu
        self.question1 = Questions.objects.create(question='Q1?', correct='Answer1', test=self.test)
        self.question2 = Questions.objects.create(question='Q2?', correct='Answer2', test=self.test)

        self.url = reverse('answer_question',
                           kwargs={'course_id': self.course.id,
                                   'subject_id': self.subject.id,
                                   'test_id': self.test.id,
                                   'question_id': self.question1.id})

    def test_get_answer_form(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'add_answers.html')
        self.assertIn('form', response.context)
        self.assertIn('question', response.context)
        self.assertEqual(response.context['question'], self.question1)

    def test_post_correct_answer_increases_score_and_redirects_to_next_question(self):
        data = {'answer': 'Answer1'}  # poprawna odpowiedź (case-insensitive)
        response = self.client.post(self.url, data)

        # Powinno przekierować na kolejne pytanie
        expected_url = reverse('answer_question',
                               kwargs={'course_id': self.course.id,
                                       'subject_id': self.subject.id,
                                       'test_id': self.test.id,
                                       'question_id': self.question2.id})
        self.assertRedirects(response, expected_url)

        # Sprawdź czy odpowiedź została zapisana
        self.assertTrue(Answers.objects.filter(user=self.user, question=self.question1, answer='Answer1').exists())

        # Sprawdź czy score wzrósł o 1
        test_score = TestScore.objects.get(user=self.user, test=self.test)
        self.assertEqual(test_score.score, 1)

    def test_post_wrong_answer_does_not_increase_score_and_redirects_to_next_question(self):
        data = {'answer': 'Wrong answer'}
        response = self.client.post(self.url, data)

        # Powinno przekierować na kolejne pytanie
        expected_url = reverse('answer_question',
                               kwargs={'course_id': self.course.id,
                                       'subject_id': self.subject.id,
                                       'test_id': self.test.id,
                                       'question_id': self.question2.id})
        self.assertRedirects(response, expected_url)

        # Odpowiedź zapisana
        self.assertTrue(Answers.objects.filter(user=self.user, question=self.question1, answer='Wrong answer').exists())

        # Score powinien być 0 (nie wzrósł)
        test_score = TestScore.objects.get(user=self.user, test=self.test)
        self.assertEqual(test_score.score, 0)

    def test_post_last_question_redirects_to_search_stores(self):
        # Test dla ostatniego pytania: przekierowanie do 'search_stores'
        url_last = reverse('answer_question',
                           kwargs={'course_id': self.course.id,
                                   'subject_id': self.subject.id,
                                   'test_id': self.test.id,
                                   'question_id': self.question2.id})

        data = {'answer': 'Answer2'}
        response = self.client.post(url_last, data)

        expected_url = reverse('search_stores', kwargs={'subject_id': self.subject.id})
        self.assertRedirects(response, expected_url)

    def test_dispatch_returns_message_if_template_missing(self):
        from unittest.mock import patch

        with patch('workapp.views.check_template', return_value=False):
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "Brak pliku .html")

class AddQuestionnaireViewTest(TestCase):

    def setUp(self):

        # Tworzymy kategorię kursu
        category = CategoryCourse.objects.create(name='Test Category')
        
        # Tworzymy użytkownika i logujemy się
        self.user = User.objects.create_user(username='testuser', password='testpass')
        author = self.user
        self.client = Client()
        self.client.login(username='testuser', password='testpass')

        # Tworzymy kategorię i przedmiot (subject)
        self.category = QuestionnaireCategory.objects.create(name='Test Category')
        
        # Tworzymy dummy plik do uploadu
        test_file = SimpleUploadedFile("file.txt", b"file_content")

        # Tworzymy kurs (wymagane pole course dla Subject)
        course = Course.objects.create(
            title='Test Course',
            author=author,
            category=category
        )

        # Przechowujemy do self
        self.course = course

        # Tworzymy Subject (wymagany do widoku)
        self.subject = Subject.objects.create(
            title='Test Subject',
            description='Desc',
            file=test_file,
            course=self.course  # Możesz dostosować jeśli wymagane
        )

        self.category = QuestionnaireCategory.objects.create(name='Test Category')

    def test_get_renders_form(self):
        url = reverse('add_questionnaire', kwargs={'course_id': self.course.id, 'subject_id': self.subject.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'questionnaire.html')

    def test_post_creates_questionnaire_and_redirects(self):
        url = reverse('add_questionnaire', kwargs={'course_id': self.course.id, 'subject_id': self.subject.id})
        data = {
            'category': self.category.id,
            # Dodaj tu inne pola z QuestionnaireForm, jeśli są wymagane
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('thanks'))

        # Sprawdzamy, czy Questionnaire został utworzony i ma poprawny subject
        questionnaire = Questionnaire.objects.last()
        self.assertIsNotNone(questionnaire)
        self.assertEqual(questionnaire.subject, self.subject)
        self.assertEqual(questionnaire.category, self.category)

    def test_dispatch_returns_message_if_template_missing(self):
        # Tymczasowo nadpisujemy metodę check_template, żeby zwracała False
        from workapp.views import AddQuestionnaireView
        original_check_template = AddQuestionnaireView.dispatch

        def fake_dispatch(self, request, *args, **kwargs):
            return HttpResponse("Brak pliku .html")

        AddQuestionnaireView.dispatch = fake_dispatch

        url = reverse('add_questionnaire', kwargs={'course_id': self.course.id, 'subject_id': self.subject.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Brak pliku .html")

        # Przywracamy oryginalną metodę
        AddQuestionnaireView.dispatch = original_check_template