from django.contrib import admin
from django.urls import path
from scraping.views import scrape_images_view, check_task_status, get_scraped_images, export_db

urlpatterns = [
    path('admin/', admin.site.urls),
    path('scrape_images/', scrape_images_view, name='scrape_images'),
    path('check_task/', check_task_status, name='check_task_status'),
    path('get_scraped_images/', get_scraped_images, name='get_scraped_images'),
    path('export_db/', export_db, name='export_db'),  
]
