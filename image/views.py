import requests
from django.db.models import Case, When
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt

from image_recommender.settings import BASE_DIR

from .models import Image


# Create your views here.
def home(request):
    context = request.session.get('context')
    if context is not None:
        input_img_id = context['input_img_id']
        image = Image.objects.get(id=input_img_id)
        top1_img = Image.objects.get(id=context['recommendations_id'][0])
        recommendations = Image.objects.filter(
            id__in=context['recommendations_id']).annotate(order=Case(*[
                When(id=img_id, then=ord)
                for ord, img_id in enumerate(context['recommendations_id'])
            ])).order_by('order')
        img_context = {
            'input_img': image,
            'top1_img': top1_img,
            'recommendations': recommendations
        }
        request.session.pop('context')
    else:
        img_context = {}
    return render(request, 'image.html', img_context)


def get_recommendations(query_image: Image):
    data = {'image_path': query_image.to_query()['image_path']}

    response = requests.post(url='http://127.0.0.1:8002/recommend-image/',
                             json=data)

    response.raise_for_status()
    image_results = response.json()
    return image_results['image_id']


@csrf_exempt
def recommend_imgs(request):
    if request.method == 'POST':
        file = request.FILES.get('images')
        try:
            # upload to db
            image = Image(source='user', image=file)
            image.full_clean()
            image.save()
            # recommend images
            recommendations_img_id = get_recommendations(image)
            context = {
                'input_img_id': str(image.id),
                'recommendations_id': recommendations_img_id,
            }
            request.session['context'] = context
            return redirect('home')
        except Exception as e:
            raise Exception(e)
