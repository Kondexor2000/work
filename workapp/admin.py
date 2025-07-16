from django.contrib import admin
from .models import *

# Register your models here.

@admin.register(LoginLog)
class LoginLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'ip_address', 'timestamp')
    search_fields = ('user__username', 'ip_address')

class CategoryEmployAdmin(admin.ModelAdmin):
    list_display = ['name']

admin.site.register(CategoryEmploy, CategoryEmployAdmin)

class CategoryCourseAdmin(admin.ModelAdmin):
    list_display = ['name']

admin.site.register(CategoryCourse, CategoryCourseAdmin)

class TagCourseAdmin(admin.ModelAdmin):
    list_display = ['name']

admin.site.register(TagCourse, TagCourseAdmin)

class QuestionnaireAdmin(admin.ModelAdmin):
    list_display = ['name']

admin.site.register(QuestionnaireCategory, QuestionnaireAdmin)

class TagPortfolioAdmin(admin.ModelAdmin):
    list_display = ['name']

admin.site.register(TagPortfolio, TagPortfolioAdmin)

class TagBusinessAdmin(admin.ModelAdmin):
    list_display = ['name']

admin.site.register(TagBusiness, TagBusinessAdmin)