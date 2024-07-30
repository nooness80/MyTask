import json
import io
import zipfile
import uuid
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from .tasks import scrape_images
from .models import ScrapedImage
import os
import subprocess
import tempfile
import base64
from django.conf import settings
import psycopg2

@csrf_exempt
def scrape_images_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        search_term = data.get('search_term')
        num_images = data.get('num_images')

        if not search_term or not num_images:
            return JsonResponse({'error': 'Invalid input'}, status=400)

        task_id = str(uuid.uuid4())
        scrape_images.delay(search_term, num_images, task_id)

        # Initialize progress in Redis
        cache.set(f'{task_id}_progress', 0)
        cache.set(f'{task_id}_status', 'in progress')

        return JsonResponse({'task_id': task_id}, status=200)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

def check_task_status(request):
    task_id = request.GET.get('task_id')
    if not task_id:
        return JsonResponse({'error': 'No task ID provided'}, status=400)

    status = cache.get(f'{task_id}_status', 'in progress')
    progress = cache.get(f'{task_id}_progress', 0)

    return JsonResponse({'status': status, 'progress': progress}, status=200)

@csrf_exempt
def get_scraped_images(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        task_id = data.get('task_id')

        if not task_id:
            return JsonResponse({'error': 'Invalid input'}, status=400)

        # Retrieve images from the database
        images = ScrapedImage.objects.filter(task_id=task_id)

        if not images:
            return JsonResponse({'error': 'No images found for this task'}, status=404)

        # Create a zip file in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            for image in images:
                zip_file.writestr(f"{image.filename}", image.image.read())

        # Move the buffer's pointer to the beginning
        zip_buffer.seek(0)

        # Create the HttpResponse object with the appropriate headers
        response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename=scraped_images_{task_id}.zip'

        return response

    return JsonResponse({'error': 'Invalid request method'}, status=405)
    
@csrf_exempt
def export_db(request):
    if request.method == 'POST':
        try:
            db_url = os.getenv('DATABASE_URL')
            with tempfile.NamedTemporaryFile(suffix='.sql') as temp_file:
                subprocess.check_call(['pg_dump', db_url, '-f', temp_file.name])
                temp_file.seek(0)
                file_data = temp_file.read()

            response = HttpResponse(file_data, content_type='application/sql')
            response['Content-Disposition'] = 'attachment; filename=backup.sql'
            return response
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)
