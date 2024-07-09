import io
from argparse import ArgumentParser
from typing import Optional

import torch
import uvicorn
from fastapi import FastAPI
from loguru import logger
from PIL import Image, ImageOps
from pydantic import BaseModel
from torchvision import transforms


def arg_parse():
    parser = ArgumentParser()
    parser.add_argument('--host', type=str, default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--apply-gs', action='store_true')
    parser.add_argument('--gs-bucket-name', type=str, required=None)
    parser.add_argument('--gs-credential', type=str, required=None)
    return parser.parse_args()


class ImageLoader:

    def __init__(self,
                 apply_gs: bool = False,
                 gs_bucket_name: Optional[str] = None,
                 gs_credential: Optional[str] = None):
        self.apply_gs = apply_gs
        if self.apply_gs:
            from google.cloud import storage
            storage_client = storage.Client.from_service_account_json(
                gs_credential)
            self.bucket = storage_client.bucket(gs_bucket_name)

    def load(self, img_file):
        if not self.apply_gs:
            image = Image.open(img_file)
        else:
            blob = self.bucket.blob(img_file)
            image_content = io.BytesIO(blob.download_as_bytes())
            image = Image.open(image_content)
        image = ImageOps.exif_transpose(image)
        return image


class ImageInfo(BaseModel):
    image_path: str


app = FastAPI()
args = arg_parse()

logger.info('Start Loading DinoV2:dinov2_vitl14!')
dinov2_model = torch.hub.load('facebookresearch/dinov2',
                              'dinov2_vitl14').to(torch.device('cuda:0'))
patch_size = dinov2_model.patch_size
transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

logger.info('Start setting ImageLoader')
img_loader = ImageLoader(apply_gs=args.apply_gs,
                         gs_bucket_name=args.gs_bucket_name,
                         gs_credential=args.gs_credential)
logger.info('Start Serving!')


def calculate_size(image, target_size: int = 1024, patch_size: int = 14):
    target_size = patch_size * (target_size // patch_size)
    width, height = image.size
    ratio = target_size / max(width, height)
    resized_width = int(width * ratio)
    resized_height = int(height * ratio)
    if width > height:
        resized_height = patch_size * (resized_height // patch_size)
    elif width < height:
        resized_width = patch_size * (resized_width // patch_size)
    else:
        assert resized_width == resized_height
    return (resized_width, resized_height)


@torch.inference_mode()
def create_embeddings(image):
    resized_width, resized_height = calculate_size(image)
    image = image.resize((resized_width, resized_height))
    trns_img = transform(image)
    features = dinov2_model(trns_img.unsqueeze(0).to(torch.device('cuda:0')))
    return features.view(-1).cpu().numpy()


@app.post('/create-image-embedding/')
async def create_image_embedding(img_info: ImageInfo):
    image = img_loader.load(img_file=img_info.image_path)
    img_embeddings = create_embeddings(image)
    return {'embedding': img_embeddings.tolist()}


if __name__ == '__main__':
    uvicorn.run(app, host=args.host, port=args.port)
