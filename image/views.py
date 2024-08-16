import json
from typing import Optional

import requests
from django.db.models import Case, When
from django.http import JsonResponse
from django.shortcuts import render

from .models import Image


# Create your views here.
def home(request):
    return render(request, 'image.html')


def get_recommendations(query_image: Image,
                        coords_info: Optional[dict] = None):
    data = {
        'image_path': query_image.to_query()['image_path'],
        'coords_info': coords_info
    }
    response = requests.post(url='http://127.0.0.1:8002/recommend-image/',
                             json=data)

    response.raise_for_status()
    image_results = response.json()
    return image_results


def recommend_imgs(request):
    if request.method == 'POST':
        image_file = request.FILES.get('image')
        image = Image(source='user', image=image_file)
        image.full_clean()
        image.save()

        coords_info = request.POST.get('coords')
        coords_info = json.loads(coords_info) if coords_info else None
        recommendation_img_ids = get_recommendations(image, coords_info)
        recommendation_imgs = Image.objects.filter(
            id__in=recommendation_img_ids).annotate(order=Case(*[
                When(id=img_id, then=ord)
                for ord, img_id in enumerate(recommendation_img_ids)
            ])).order_by('order')
        return JsonResponse(
            data={'image_url': [img.image.url for img in recommendation_imgs]})
