from django.contrib import admin
from .models import ScrapedImage

@admin.register(ScrapedImage)
class ScrapedImageAdmin(admin.ModelAdmin):
    list_display = ('filename', 'search_term', 'task_id', 'created_at')
    list_filter = ('search_term', 'task_id', 'created_at')
    search_fields = ('filename', 'search_term', 'task_id')