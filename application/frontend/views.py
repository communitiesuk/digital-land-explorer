from flask import (
    Blueprint,
    render_template
)

from application.models import Organisation

frontend = Blueprint('frontend', __name__, template_folder='templates')


@frontend.route('/')
def index():
    return render_template('index.html')


@frontend.route('/local-authorities')
def local_authorities():
    las = Organisation.query.filter(Organisation.organisation.like('local-authority-%')).all()
    return render_template('local-authorities.html', local_authorities=las)


@frontend.route('/local-authorities/<org_id>')
def local_authority(org_id):
    la = Organisation.query.get(org_id)
    return render_template('local-authority.html', local_authority=la)


@frontend.context_processor
def asset_path_context_processor():
    return {'asset_path': '/static/govuk_template'}
