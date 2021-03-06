# -*- coding: utf-8 -*-
import json
import os


if os.environ.get('VCAP_SERVICES') is not None:
    vcap_services = json.loads(os.environ.get('VCAP_SERVICES'))
    os.environ['DATABASE_URL'] = vcap_services['postgres'][0]['credentials']['uri']
    os.environ['SECRET_KEY'] = vcap_services['user-provided'][0]['credentials']['SECRET_KEY']
    os.environ['MAPBOX_TOKEN'] = vcap_services['user-provided'][0]['credentials']['MAPBOX_TOKEN']
    os.environ['S3_REGION'] = vcap_services['user-provided'][0]['credentials']['S3_REGION']
    os.environ['S3_BUCKET'] = vcap_services['user-provided'][0]['credentials']['S3_BUCKET']
    os.environ['AWS_ACCESS_KEY_ID'] = vcap_services['user-provided'][0]['credentials']['AWS_ACCESS_KEY_ID']
    os.environ['AWS_SECRET_ACCESS_KEY'] = vcap_services['user-provided'][0]['credentials']['AWS_SECRET_ACCESS_KEY']


class Config(object):
    APP_ROOT = os.path.abspath(os.path.dirname(__file__))
    PROJECT_ROOT = os.path.abspath(os.path.join(APP_ROOT, os.pardir))
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    MAPBOX_TOKEN=os.getenv('MAPBOX_TOKEN')
    JSONIFY_PRETTYPRINT_REGULAR=False
    S3_REGION = os.getenv('S3_REGION')
    S3_BUCKET = os.getenv('S3_BUCKET')


class DevelopmentConfig(Config):
    DEBUG = True
    WTF_CSRF_ENABLED = False


class TestConfig(Config):
    TESTING = True
