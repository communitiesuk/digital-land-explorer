import os
from flask_migrate import Migrate

from application.factory import create_app
from application.extensions import db
from application.models import *

app = create_app(os.getenv('FLASK_CONFIG') or 'config.DevelopmentConfig')

migrate = Migrate(app, db)

@app.shell_context_processor
def make_shell_context():
    return dict(app=app, db=db)

