from django.contrib import admin
from .models import *

# Register your models here.

class CategoryEmployAdmin(admin.ModelAdmin):
    list_display = ['name']

admin.site.register(CategoryEmploy, CategoryEmployAdmin)

class CategoryCourseAdmin(admin.ModelAdmin):
    list_display = ['name']

admin.site.register(CategoryCourse, CategoryCourseAdmin)

class TagCourseAdmin(admin.ModelAdmin):
    list_display = ['name']

admin.site.register(TagCourse, TagCourseAdmin)

class TagPortfolioAdmin(admin.ModelAdmin):
    list_display = ['name']

admin.site.register(TagPortfolio, TagPortfolioAdmin)

class TagBusinessAdmin(admin.ModelAdmin):
    list_display = ['name']

admin.site.register(TagBusiness, TagBusinessAdmin)