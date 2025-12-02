from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class LoginLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField()
    timestamp = models.DateTimeField(auto_now_add=True)

# === HR i Oferty pracy ===

class TagBusiness(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
class Business(models.Model):
    name = models.CharField(max_length=255)
    tags = models.ManyToManyField(TagBusiness, blank=True)


    def __str__(self):
        return self.name

class HR(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField()
    number_phone = models.CharField(max_length=20)
    business = models.ManyToManyField(Business, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
class CategoryEmploy(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class OffersJob(models.Model):
    title = models.CharField(max_length=255)
    business = models.ForeignKey(Business, on_delete=models.CASCADE)
    hr = models.ForeignKey(HR, on_delete=models.CASCADE)
    tags = models.ManyToManyField(TagBusiness, blank=True)
    category = models.ForeignKey(CategoryEmploy, on_delete=models.CASCADE)
    file = models.FileField(upload_to='uploads/')

    def __str__(self):
        return self.title
    
class OffersJobUser(models.Model):
    offer = models.ForeignKey(OffersJob, on_delete=models.CASCADE)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_accept = models.BooleanField(default=False)

# === Kursy i Edukacja ===

class TagCourse(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
class CategoryCourse(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Course(models.Model):
    title = models.CharField(max_length=255)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.ManyToManyField(TagCourse, blank=True)
    category = models.ForeignKey(CategoryCourse, on_delete=models.CASCADE)

    def __str__(self):
        return self.title
    
class Subject(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    file = models.FileField(upload_to='uploads/')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

class Certificate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

# === Testy i Wyniki ===

class Test(models.Model):
    title = models.CharField(max_length=255)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, null=True, blank=True)
    is_finish = models.BooleanField(default=False)

    def __str__(self):
        return self.title
    
class Questions(models.Model):
    question = models.CharField(max_length=255)
    correct = models.TextField()
    test = models.ForeignKey(Test, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.question
    
class Answers(models.Model):
    answer = models.TextField()
    question = models.ForeignKey(Questions, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

class TestScore(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=5, decimal_places=2)
    minimum = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"{self.user} - {self.test} - {self.score}"

# === Użytkownik: CV i doświadczenie ===

class CV(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField()
    number_phone = models.CharField(max_length=20)
    street = models.CharField(max_length=100, default="Kowalskiego")
    number_house = models.CharField(max_length=10, default="1")
    code = models.CharField(max_length=10, default="64-920")
    city = models.CharField(max_length=50, default="Poznań")

    def __str__(self):
        return self.title

class Experience(models.Model):
    cv = models.ForeignKey(CV, on_delete=models.CASCADE)
    company = models.CharField(max_length=255)
    position = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.position} at {self.company}"
    
class Education(models.Model):
    cv = models.ForeignKey(CV, on_delete=models.CASCADE)
    fields_of_state = models.CharField(max_length=255)
    place = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.fields_of_state} at {self.place}"
    
class Skills(models.Model):
    cv = models.ForeignKey(CV, on_delete=models.CASCADE)
    skill = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.skill}"
    
class Hobby(models.Model):
    cv = models.ForeignKey(CV, on_delete=models.CASCADE)
    hobby = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.hobby}"
    
class QuestionnaireCategory(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name}"
    
class Questionnaire(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    category = models.ForeignKey(QuestionnaireCategory, on_delete=models.CASCADE, null=True, blank=True)

# === Portfolio i projekty ===

class TagPortfolio(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Portfolio(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tags = models.ManyToManyField(TagPortfolio, blank=True)
    title = models.CharField(max_length=255)

    def __str__(self):
        return self.title

class Projects(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='uploads/')

    def __str__(self):
        return self.title

class Link(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, null=True, blank=True)
    url = models.URLField()

    def __str__(self):
        return self.url
    
class Transmition(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    leaders = models.ForeignKey(User, on_delete=models.CASCADE, related_name='led_transmitions')
    participants = models.ManyToManyField(User, related_name='participated_transmitions', blank=True)
    start = models.DateTimeField()
    end = models.DateTimeField()

    def __str__(self):
        return self.title
    
class Comment(models.Model):
    description = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    transmition = models.ForeignKey(Transmition, on_delete=models.CASCADE)

class Opinion(models.Model):
    description = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)