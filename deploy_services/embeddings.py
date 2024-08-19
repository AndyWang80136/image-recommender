import io
from argparse import ArgumentParser
from typing import Optional

import torch
import uvicorn
from fastapi import FastAPI
from loguru import logger
from PIL import Image, ImageOps
from pydantic import BaseModel
from torchvision.transforms import v2


def arg_parse():
    parser = ArgumentParser()
    parser.add_argument('--host', type=str, default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--apply-gs', action='store_true')
    parser.add_argument('--gs-bucket-name', type=str, required=None)
    parser.add_argument('--gs-credential', type=str, required=None)
    parser.add_argument('--image-size', type=int, default=448)
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

logger.info(f'Start Loading DinoV2:dinov2_vitb14!')
dinov2_model = torch.hub.load('facebookresearch/dinov2',
                              'dinov2_vitb14').to(torch.device('cuda:0'))

patch_size = dinov2_model.patch_size
embedding_dim = dinov2_model.embed_dim
logger.info(
    f'Finish Loading DinoV2:dinov2_vitb14: patch-size: {patch_size} embedding: {embedding_dim}'
)

img_transform = v2.Compose([
    v2.Resize(size=args.image_size),
    v2.ToTensor(),
    v2.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225))
])

logger.info('Start setting ImageLoader')
img_loader = ImageLoader(apply_gs=args.apply_gs,
                         gs_bucket_name=args.gs_bucket_name,
                         gs_credential=args.gs_credential)
logger.info('Start Serving!')


@torch.inference_mode()
def generate_embedding(image: Image.Image, embedding_type: str = 'image'):
    assert embedding_type in ('image', 'patch')
    trns_img = img_transform(image)
    _, height, width = trns_img.size()
    trns_img = trns_img[:, :(height // patch_size) *
                        patch_size, :(width // patch_size) *
                        patch_size].unsqueeze(0).to(torch.device('cuda:0'))
    if embedding_type == 'image':
        features = dinov2_model(trns_img)
        grid_shape = (1, )
    else:
        features = dinov2_model.forward_features(
            trns_img)['x_norm_patchtokens']
        grid_shape = (height // patch_size, width // patch_size)

    return dict(embedding=features[0].cpu().numpy().tolist(),
                embedding_shape=(*grid_shape, features.size(-1)),
                image_shape=[height, width],
                patch_size=patch_size)


@app.post('/generate-image-embedding/')
async def generate_image_embedding(img_info: ImageInfo):
    image = img_loader.load(img_file=img_info.image_path)
    embedding_info = generate_embedding(image, embedding_type='image')
    return embedding_info


@app.post('/generate-patch-embedding/')
async def generate_patch_embedding(img_info: ImageInfo):
    image = img_loader.load(img_file=img_info.image_path)
    embedding_info = generate_embedding(image, embedding_type='patch')
    return embedding_info


if __name__ == '__main__':
    uvicorn.run(app, host=args.host, port=args.port)
