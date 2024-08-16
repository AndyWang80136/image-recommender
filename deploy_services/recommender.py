import os
from argparse import ArgumentParser
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import requests
import uvicorn
from fastapi import FastAPI
from loguru import logger
from pydantic import BaseModel
from pymilvus import MilvusClient

IMAGE_EMBEDDING_API = 'http://127.0.0.1:8001/create-image-embedding/'
PATCH_EMBEDDING_API = 'http://127.0.0.1:8001/create-patch-embedding/'


class QueryImage(BaseModel):
    image_path: str
    coords_info: Optional[dict]


def arg_parse():
    parser = ArgumentParser()
    parser.add_argument('--fg-pipeline', type=str, default='fg-pipeline.pkl')
    parser.add_argument('--db-file', type=str, default='embedding.db')
    parser.add_argument('--host', type=str, default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8002)
    parser.add_argument('--top-k', type=int, default=10)
    return parser.parse_args()


def load_db(db_file: str):
    logger.info(f'Load db: {db_file}')
    if Path(f'.{db_file}.lock').exists():
        os.remove(f'.{db_file}.lock')
    return MilvusClient(db_file)


def load_fg_pipeline(pkl_file: str):
    with open(pkl_file, 'rb') as fp:
        return joblib.load(fp)


def resize_coords(coords: dict, coords_img_size: tuple,
                  target_img_size: tuple):
    coords_img_height, coords_img_width = coords_img_size
    target_img_height, target_img_width = target_img_size
    height_ratio = target_img_height / coords_img_height
    width_ratio = target_img_width / coords_img_width
    return dict(
        x1=coords['x1'] * width_ratio,
        y1=coords['y1'] * height_ratio,
        x2=coords['x2'] * width_ratio,
        y2=coords['y2'] * height_ratio,
    )


def locate_focus_patches(
    embedding: np.ndarray,
    coords: dict,
    patch_size: int,
    image_shape: tuple,
    embedding_shape: tuple,
):
    x1, y1, x2, y2 = coords['x1'], coords['y1'], coords['x2'], coords['y2']
    grid_size = (image_shape[0] // patch_size, image_shape[1] // patch_size)
    grid_x = int(x1 // patch_size), min(int(x2 // patch_size),
                                        grid_size[1] - 1)
    grid_y = int(y1 // patch_size), min(int(y2 // patch_size),
                                        grid_size[0] - 1)
    grid_index = [(y, x) for x in range(grid_x[0], grid_x[1] + 1, 1)
                  for y in range(grid_y[0], grid_y[1] + 1, 1)]
    y_values, x_values = zip(*grid_index)
    fg_embedding = fg_pipeline.transform(np.asarray(embedding))
    embedding_array = np.asarray(embedding)
    embedding_array[~(fg_embedding.ravel() > 0.5), :] = 0
    focus_embedding = embedding_array.reshape(*embedding_shape)[y_values,
                                                                x_values, :]
    return focus_embedding[focus_embedding.any(axis=1), :]


def get_embedding(image_path: str, embedding_type: str):
    assert embedding_type in ['image', 'patch']
    api_url = IMAGE_EMBEDDING_API if embedding_type == 'image' else PATCH_EMBEDDING_API
    response = requests.post(api_url, json=dict(image_path=image_path))
    response.raise_for_status()
    return response.json()


def recommend_imgs_by_image_embedding(image_path: str):
    embedding_info = get_embedding(image_path=image_path,
                                   embedding_type='image')
    results = db.search('image_embeddings',
                        data=[embedding_info['embedding']],
                        output_fields=['image_id'],
                        search_params={'metric_type': 'COSINE'},
                        limit=args.top_k)[0]
    return [info['entity']['image_id'] for info in results]


def recommend_imgs_by_patch_embedding(image_path: str, focus_area: dict):
    embedding_info = get_embedding(image_path=image_path,
                                   embedding_type='patch')
    patch_embedding, image_shape, patch_size, embedding_shape = embedding_info[
        'embedding'], embedding_info['image_shape'], embedding_info[
            'patch_size'], embedding_info['embedding_shape']
    target_coords = resize_coords(coords=dict(x1=focus_area['x1'],
                                              y1=focus_area['y1'],
                                              x2=focus_area['x2'],
                                              y2=focus_area['y2']),
                                  coords_img_size=(focus_area['height'],
                                                   focus_area['width']),
                                  target_img_size=image_shape)
    focus_patches_embedding = locate_focus_patches(
        embedding=patch_embedding,
        coords=target_coords,
        patch_size=patch_size,
        image_shape=image_shape,
        embedding_shape=embedding_shape)

    if not focus_patches_embedding.size:
        return recommend_imgs_by_image_embedding(image_path=image_path)

    distances = []
    all_images = db.query(collection_name='image_embeddings',
                          filter='id > 0',
                          output_fields=['image_id'])
    for image_in_db in all_images:
        image_id = image_in_db['image_id']
        results = db.search(collection_name='patch_embeddings',
                            data=focus_patches_embedding,
                            filter=f'image_id == "{image_id}"',
                            output_fields=['image_id'],
                            limit=1)
        mean_distances = [r[0]['distance'] for r in results]
        distances.append({
            'image_id': image_id,
            'distance': np.mean(mean_distances)
        })
    sorted_distance = sorted(distances,
                             key=lambda a: a['distance'],
                             reverse=True)

    return [i['image_id'] for i in sorted_distance][:args.top_k]


def recommend_imgs(image_path: str, focus_area: Optional[dict] = None):
    return recommend_imgs_by_patch_embedding(
        image_path, focus_area
    ) if focus_area is not None else recommend_imgs_by_image_embedding(
        image_path)


app = FastAPI()
args = arg_parse()
db = load_db(db_file=args.db_file)
fg_pipeline = load_fg_pipeline(pkl_file=args.fg_pipeline)


@app.post('/recommend-image/')
async def recommend_image(query_img: QueryImage):
    img_ids = recommend_imgs(image_path=query_img.image_path,
                             focus_area=query_img.coords_info)
    return img_ids


if __name__ == '__main__':
    uvicorn.run(app, host=args.host, port=args.port)
