from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class LoginLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField()
    timestamp = models.DateTimeField(auto_now_add=True)

# === Portfolio i projekty ===

class TagPortfolio(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Link(models.Model):
    tags = models.ForeignKey(TagPortfolio, on_delete=models.CASCADE, null=True, blank=True)
    description = models.TextField(blank=True, null=True)