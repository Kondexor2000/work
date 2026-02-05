from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class LoginLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField()
    timestamp = models.DateTimeField(auto_now_add=True)

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