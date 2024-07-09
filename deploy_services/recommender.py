import os
from argparse import ArgumentParser
from pathlib import Path

import requests
import uvicorn
from fastapi import FastAPI
from loguru import logger
from pydantic import BaseModel
from pymilvus import MilvusClient


class QueryImage(BaseModel):
    image_path: str


def arg_parse():
    parser = ArgumentParser()
    parser.add_argument('--db-file', type=str, default='embedding.db')
    parser.add_argument('--host', type=str, default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8002)
    parser.add_argument('--top-k', type=int, default=10)
    return parser.parse_args()


def load_db(db_file):
    logger.info(f'Load db: {db_file}')
    if Path(f'.{db_file}.lock').exists():
        os.remove(f'.{db_file}.lock')
    return MilvusClient(db_file)


app = FastAPI()
args = arg_parse()
db = load_db(db_file=args.db_file)


@app.post('/recommend-image/')
async def recommend_image(query_img: QueryImage):
    data = {'image_path': query_img.image_path}
    response = requests.post(
        url='http://127.0.0.1:8001/create-image-embedding/', json=data)
    if response.status_code == 200:
        results = response.json()
        embedding = results['embedding']
        results = db.search('image_embeddings',
                            data=[embedding],
                            output_fields=['image_id'],
                            search_params={'metric_type': 'COSINE'},
                            limit=args.top_k)[0]
        return {'image_id': [info['entity']['image_id'] for info in results]}
    else:
        raise Exception(response.status_code)


if __name__ == '__main__':
    uvicorn.run(app, host=args.host, port=args.port)
