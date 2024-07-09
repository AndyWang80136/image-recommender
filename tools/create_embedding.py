import os
import sys

sys.path.insert(0, '.')
import asyncio
from pathlib import Path
from typing import List

import aiohttp
import django
from loguru import logger
from pymilvus import MilvusClient

os.environ['DJANGO_SETTINGS_MODULE'] = 'image_recommender.settings'
django.setup()

from argparse import ArgumentParser

from image.models import Image

MODEL_API = '/create-image-embedding/'


def arg_parse():
    parser = ArgumentParser()
    parser.add_argument('--db-file', type=str, default='embedding.db')
    parser.add_argument('--model-url', type=str, default='http://127.0.0.1')
    parser.add_argument('--model-port', type=int, default=8000)
    parser.add_argument('--model-api', type=str, default=MODEL_API)
    parser.add_argument('--embedding-size', type=int, default=1024)
    return parser.parse_args()


def create_vector_db(db_file):
    logger.info(f'Create ')
    logger.info(f'Create DB: {db_file}')
    logger.info(
        f'Create Collection: "image_embeddings" shape: {args.embedding_size}')
    if Path(f'.{db_file}.lock').exists():
        os.remove(f'.{db_file}.lock')
    client = MilvusClient(db_file)
    if not client.has_collection('image_embeddings'):
        client.create_collection(
            collection_name='image_embeddings',
            vector_field_name='vector',
            dimension=args.embedding_size,
            auto_id=True,
            enable_dynamic_field=True,
            metric_type='COSINE',
        )
    return client


async def model_infer(session, url, info):
    async with session.post(url, json={'image_path':
                                       info['image_path']}) as response:
        result = await response.json()
        return result


async def create_embedding(args, img_info: List[str]):
    db = create_vector_db(db_file=args.db_file)
    model_url = f'{args.model_url}:{args.model_port}{args.model_api}'
    async with aiohttp.ClientSession() as session:
        tasks = [model_infer(session, model_url, info) for info in img_info]
        results = await asyncio.gather(*tasks)

    for info, result in zip(img_info, results):
        db.insert('image_embeddings', {'vector': result['embedding'], **info})

    logger.info(f'Create {len(img_info)} images embeddings')


if __name__ == '__main__':
    args = arg_parse()
    img_info = [
        image.to_query() for image in Image.objects.filter(source='example')
    ]
    asyncio.run(create_embedding(args=args, img_info=img_info))
