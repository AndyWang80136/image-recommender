# Django Image Recommender
A Django application that recommends relevant images based on the user-uploaded image.

## Demo [[Video]](https://drive.google.com/file/d/1aRk2uRKnTxC_2GdqQUv7C3YQ1h-ZB1CF)

<table>
  <tr>
    <td>
      <figure>
        <img alt="Image-Recommender-v1-step1" src="https://github.com/user-attachments/assets/427889f8-2888-42b1-a747-0ee32bb245de">
        <figcaption>Step 1: Drag and drop an image file</figcaption>
      </figure>
    </td>
    <td>
      <figure>
        <img alt="Image-Recommender-v1-step2" src="https://github.com/user-attachments/assets/b0ffab5b-e7d5-4fec-9cd7-8bb82474434c">
        <figcaption>Step 2: Click Search button</figcaption>
      </figure>
    </td>
  </tr>
  <tr>
    <td>
      <figure>
        <img alt="Image-Recommender-v1-step3" src="https://github.com/user-attachments/assets/4e2f3496-b773-4966-b487-99f1584bf186">
        <figcaption>Step 3: Browse the recommended images</figcaption>
      </figure>
    </td>
    <td>
      <figure>
        <img alt="Image-Recommender-v1-step4" src="https://github.com/user-attachments/assets/2adc0914-03db-4b6e-b9fc-2e94936cc19f">
        <figcaption>Step 4: Click Draw button, draw an area, and search</figcaption>
      </figure>
    </td>
  </tr>
  <tr>
    <td>
      <figure>
        <img alt="Image-Recommender-v1-step5" src="https://github.com/user-attachments/assets/619241ea-7612-4310-9c54-203ab6317d8b">
        <figcaption>Step 5: Click Clear button to draw again</figcaption>
      </figure>
    </td>
    <td>
      <figure>
        <img alt="Image-Recommender-v1-step6" src="https://github.com/user-attachments/assets/857f5f21-0757-4a5b-96a3-b61a7c589cf9">
        <figcaption>Step 6: Draw another area, and search</figcaption>
      </figure>
    </td>
  </tr>
</table>

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
- Model API development & deployment by FastAPI & Uvicorn

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

#### 4. Deploy and serve embedding service
```shell
# Embedding service for local file
python deploy_services/embedding.py --host '127.0.0.1' --port 8001
# Embedding service for GCS file
python deploy_services/embedding.py --host '127.0.0.1' --port 8001 --apply-gs --gs-bucket-name $GS_BUCKET_NAME  --gs-credential $GS_CREDENTIAL
```
#### 5. Generate embedding
```shell
python tools/generate_embedding.py --embedding-url 'http://127.0.0.1' --embedding-port 8001 --db-file [DB_FILE] --save-fg-pipeline [PKL_FILE] --embedding-size [EMBEDDING_SIZE]
```
#### 6. Run recommender service
```shell
python deploy_services/recommender.py --host '127.0.0.1' --port 8002 --db-file [DB_FILE] --top-k [TOP_K] --fg-pipeline [PKL_FILE]
```

#### 7. Application
Open a web browser, type `localhost:8000`

## License
[MIT License](./LICENSE)

## Contact Information
If there are any problems, please feel free to raise issues or send me an email: andy80136@gmail.com
