from django.contrib import admin
from .models import Category

class CategoriesAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}

admin.site.register(Category, CategoriesAdmin)
