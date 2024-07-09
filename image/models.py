import uuid
from pathlib import Path

from django.conf import settings
from django.db import models


# Create your models here.
def custom_image_path(instance, filename):
    image_id = str(instance.id)
    timestamp = str(instance.created_date.timestamp())
    extension = Path(filename).suffix
    return f'images/{image_id}-{timestamp}{extension}'


class Image(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    modified_date = models.DateTimeField(auto_now=True)
    created_date = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(blank=False, upload_to=custom_image_path)
    source = models.CharField(max_length=200, default='example', blank=False)

    def __str__(self):
        return f'{self.id}'

    def to_query(self):
        return {
            'image_id':
            str(self.id),
            'image_path':
            self.image.name if settings.APPLY_GS else self.image.url[1:]
        }
