import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///local.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'changeme')
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', '/var/data')
