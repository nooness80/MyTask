from django.db import models

class ScrapedImage(models.Model):
    task_id = models.UUIDField()
    filename = models.CharField(max_length=255)
    image = models.ImageField(upload_to='scraped_images/')
    created_at = models.DateTimeField(auto_now_add=True)
    search_term = models.CharField(max_length=255)  # Add this line

    def __str__(self):
        return f"{self.filename} ({self.task_id})"