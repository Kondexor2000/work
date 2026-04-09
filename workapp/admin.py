from django.contrib import admin
from .models import *
from django.contrib.admin.actions import delete_selected

# Register your models here.

@admin.register(LoginLog)
class LoginLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'ip_address', 'timestamp')
    search_fields = ('user__username', 'ip_address')

class TagPortfolioAdmin(admin.ModelAdmin):
    list_display = ['name']

admin.site.register(TagPortfolio, TagPortfolioAdmin)

class LinkAdmin(admin.ModelAdmin):
    list_display = ['description']
    actions = [delete_selected]

admin.site.register(Link, LinkAdmin)