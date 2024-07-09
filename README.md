# Django Image Recommender
A Django application that recommends relevant images based on the user-uploaded image.

## Demo [[Video]](https://drive.google.com/file/d/1sLMo2zxqNzLrfcxc3NZAg3f8Hi_FK2Am/)

<img width="50%" alt="Image-Recommender-v0-step0" src="https://github.com/AndyWang80136/image-recommender/assets/14234143/b3453b5e-512d-4d1f-ba04-0e90967ac4c2">

#### 1. Drag and drop an image file
<img width="50%" alt="Image-Recommender-v0-step1" src="https://github.com/AndyWang80136/image-recommender/assets/14234143/846114cd-5c2a-4def-80b0-02da6486e093">

#### 2. Generate an image imbedding on the fly and recommend relevant images.
<img width="50%" alt="Image-Recommender-v0-step2" src="https://github.com/AndyWang80136/image-recommender/assets/14234143/f2c52110-6774-46c3-97cf-2cf3dd92d863">

#### 3. Click to view the recommended image.
<img width="50%" alt="Image-Recommender-v0-step3" src="https://github.com/AndyWang80136/image-recommender/assets/14234143/e26de34a-eb38-4df9-9b70-9e8b98f9b859">

## Technical Reviews
### Frontend
- HTML & CSS
- Bootstrap 5
- Javascript
### Backend
- Django
- Milvus (Vector DB)
- Google Cloud Storage (GCS) 
### Data / Models / Algorithms
- Image embedding by [DINOv2](https://github.com/facebookresearch/dinov2) [(Apache License 2.0)](https://github.com/facebookresearch/dinov2?tab=readme-ov-file#license)
- Recommendation by image embedding similarity search
- FastAPI model deployment & serving

## Installation & Usage
### Installation
```shell
# Django Service
pip install -r requirements/requirements.txt 
# Model Serving
pip install -r requirements/requirements-deploy.txt
# Dev
pip install -r requirements/requirements-dev.txt
```
**DINOv2** [Installation](https://github.com/facebookresearch/dinov2?tab=readme-ov-file#installation)

### Usage
#### 1. Setup variables
- Django `SECRET_KEY` in [settings.py](./image_recommender/settings.py) or set `DJANGO_IMAGE_RECOMMENDER_SECRET_KEY` in environment variables
- Google Cloud Storage (GCS) settings in [settings.py](./image_recommender/settings.py) or set `GS_BUCKET_NAME` and `GS_CREDENTIAL` in environment variables

#### 2. Setup and start service
```shell
python manage.py makemigrations image
python manage.py migrate

# Start service
python manage.py runserver
```

#### 3. Upload own images to Django DB
```shell
python tools/upload_img_django.py --img-dir [IMAGE_DIRECTORY]
```

#### 4. Deploy and serve Model 
```shell
# Model service for local file
python deploy_services/model.py --host '127.0.0.1' --port 8001
# Model service for GCS file
python deploy_services/model.py --host '127.0.0.1' --port 8001 --apply-gs --gs-bucket-name $GS_BUCKET_NAME  --gs-credential $GS_CREDENTIAL
```
#### 5. Create image embedding
```shell
python tools/create_embedding.py --model-url 'http://127.0.0.1' --model-port 8001 --db-file [DB_FILE]
```
#### 6. Run recommender service
```shell
python deploy_services/recommender.py --host '127.0.0.1' --port 8002 --db-file [DB_FILE] --top-k [TOP_K]
```

#### 7. Application
Open a web browser, type `localhost:8000`

## License
[MIT License](./LICENSE)

## Contact Information
If there are any problems, please feel free to raise issues or send me an email: andy80136@gmail.com
