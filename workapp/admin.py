from django.contrib import admin
from .models import *

# Register your models here.

@admin.register(LoginLog)
class LoginLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'ip_address', 'timestamp')
    search_fields = ('user__username', 'ip_address')

class TagPortfolioAdmin(admin.ModelAdmin):
    list_display = ['name']

admin.site.register(TagPortfolio, TagPortfolioAdmin)