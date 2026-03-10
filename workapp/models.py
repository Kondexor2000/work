from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class LoginLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField()
    timestamp = models.DateTimeField(auto_now_add=True)

# === Testy i Wyniki ===

class Test(models.Model):
    title = models.CharField(max_length=255)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    is_finish = models.BooleanField(default=False)

    def __str__(self):
        return self.title
    
class Question(models.Model):
    question = models.CharField(max_length=255)
    correct = models.TextField()
    test = models.ForeignKey(Test, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.question
    
class Recruter(models.Model):
    candidate = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    finished = models.BooleanField(default=False)

class TestScore(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    max_score = models.IntegerField(default=0)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'test')

class Answer(models.Model):
    answer = models.TextField()
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    
# === Portfolio i projekty ===

class TagPortfolio(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Portfolio(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tags = models.ManyToManyField(TagPortfolio, blank=True)
    title = models.CharField(max_length=255)
    number_phone = models.CharField(max_length=20, blank=True)
    e_mail = models.EmailField(blank=True)

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