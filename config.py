import os

class Config(object):
    S3_BUCKET = str(os.environ.get('S3_BUCKET')) or False
