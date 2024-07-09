import os
import sys

sys.path.insert(0, '.')

from pathlib import Path

import django
from django.core.files import File

os.environ['DJANGO_SETTINGS_MODULE'] = 'image_recommender.settings'
django.setup()

from argparse import ArgumentParser
from datetime import datetime

from loguru import logger

from image.models import Image

IMG_EXT = ('*.jpg', '*.jpeg', '*.JPG', '*.PNG', '*.png')


def arg_parse():
    parser = ArgumentParser()
    parser.add_argument('--img-dir', type=str)
    return parser.parse_args()


def upload_images(img_dir: Path):
    img_cnt = 0
    for img_ext in IMG_EXT:
        for img_file in Path(img_dir).rglob(img_ext):
            with open(img_file, 'rb') as f:
                img_file = File(f)
                image = Image.objects.create(image=img_file,
                                             modified_date=datetime.now(),
                                             created_date=datetime.now())
                image.save()
                img_cnt += 1
    logger.info(f'Upload {img_cnt} images')


if __name__ == '__main__':
    args = arg_parse()
    upload_images(img_dir=args.img_dir)
