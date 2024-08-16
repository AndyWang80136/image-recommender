import sys

sys.path.insert(0, '.')

import os

import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'image_recommender.settings'
django.setup()

import asyncio
from argparse import ArgumentParser
from pathlib import Path
from typing import List

import aiohttp
import joblib
import numpy as np
from loguru import logger
from pymilvus import CollectionSchema, DataType, FieldSchema, MilvusClient
from pymilvus.milvus_client import IndexParams
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler

from image.models import Image

IMAGE_EMBEDDING_API = '/create-image-embedding/'
PATCH_EMBEDDING_API = '/create-patch-embedding/'


def arg_parse():
    parser = ArgumentParser()
    parser.add_argument('--db-file', type=str, default='embedding.db')
    parser.add_argument('--embedding-url',
                        type=str,
                        default='http://127.0.0.1')
    parser.add_argument('--embedding-port', type=int, default=8000)
    parser.add_argument('--embedding-size', type=int, default=1024)
    parser.add_argument('--save-fg-pipeline',
                        type=str,
                        default='fg-pipeline.pkl')
    return parser.parse_args()


def create_collection(
    client: MilvusClient,
    collection_name: str,
    schemas: List[FieldSchema],
    index_param: IndexParams,
):
    if client.has_collection(collection_name):
        client.drop_collection(collection_name)

    client.create_collection(collection_name=collection_name,
                             schema=CollectionSchema(
                                 fields=schemas,
                                 description=' '.join([
                                     s.capitalize()
                                     for s in collection_name.split('_')
                                 ])))

    client.create_index(collection_name=collection_name,
                        index_params=index_param)
    return client


def create_db_collections(client: MilvusClient):
    schemas = [
        FieldSchema(name="id",
                    dtype=DataType.INT64,
                    is_primary=True,
                    auto_id=True),
        FieldSchema(name="image_id", dtype=DataType.VARCHAR, max_length=200),
        FieldSchema(name="embedding",
                    dtype=DataType.FLOAT_VECTOR,
                    dim=args.embedding_size)
    ]
    index_params = MilvusClient.prepare_index_params()
    index_params.add_index(
        field_name="embedding",
        metric_type="COSINE",
        index_name="embedding_index",
    )
    client = create_collection(client=client,
                               collection_name='image_embeddings',
                               schemas=schemas,
                               index_param=index_params)
    client = create_collection(client=client,
                               collection_name='patch_embeddings',
                               schemas=schemas,
                               index_param=index_params)

    return client


def create_vector_db(db_file: str):
    logger.info(f'Create DB: {db_file}')
    logger.info(
        f'Create Collection: "image_embeddings" shape: {args.embedding_size}')
    if Path(f'.{db_file}.lock').exists():
        os.remove(f'.{db_file}.lock')
    client = MilvusClient(db_file)
    return create_db_collections(client)


def process_patch_embeddings(patch_embeddings_info: List[dict]):
    all_patch_embedding = np.vstack(
        [p['embedding'] for p in patch_embeddings_info])
    fg_pipeline = Pipeline([('pca', PCA(n_components=1)),
                            ('scaler', MinMaxScaler())])
    fg_pipeline.fit(all_patch_embedding)
    for patch_embedding in patch_embeddings_info:
        embedding = patch_embedding['embedding']
        trns_patch_embedding = fg_pipeline.transform(embedding)
        fg_mask = (trns_patch_embedding > 0.5).ravel()
        embedding = embedding[fg_mask, :]
        patch_embedding['embedding'] = embedding
    with open(args.save_fg_pipeline, 'wb') as fp:
        joblib.dump(fg_pipeline, fp)


async def get_embedding(session, url, info):
    async with session.post(url, json={'image_path':
                                       info['image_path']}) as response:
        embedding_info = await response.json()
        embedding_info['embedding'] = np.asarray(embedding_info['embedding'])
        return embedding_info


async def create_embedding(args, img_info: List[str]):
    db = create_vector_db(db_file=args.db_file)
    image_embedding_url = f'{args.embedding_url}:{args.embedding_port}{IMAGE_EMBEDDING_API}'
    patch_embedding_url = f'{args.embedding_url}:{args.embedding_port}{PATCH_EMBEDDING_API}'
    async with aiohttp.ClientSession() as session:
        image_tasks = [
            get_embedding(session, image_embedding_url, info)
            for info in img_info
        ]
        image_embedding_results = await asyncio.gather(*image_tasks)
        patch_tasks = [
            get_embedding(session, patch_embedding_url, info)
            for info in img_info
        ]
        patch_embedding_results = await asyncio.gather(*patch_tasks)

    process_patch_embeddings(patch_embedding_results)
    for info, img_embedding, patch_embedding in zip(img_info,
                                                    image_embedding_results,
                                                    patch_embedding_results):
        image_id = info['image_id']
        db.insert('image_embeddings', {
            'embedding': img_embedding.pop('embedding'),
            'image_id': image_id
        })
        db.insert('patch_embeddings', [{
            'embedding': embedding,
            'image_id': image_id
        } for embedding in patch_embedding['embedding']])
    logger.info(f'Create {len(img_info)} images embedding')


if __name__ == '__main__':
    args = arg_parse()
    img_info = [
        image.to_query() for image in Image.objects.filter(source='example')
    ]
    asyncio.run(create_embedding(args=args, img_info=img_info))
