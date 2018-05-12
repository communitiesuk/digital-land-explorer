from flask import (
    Blueprint,
    render_template,
    abort)

from application.models import Organisation, Publication

frontend = Blueprint('frontend', __name__, template_folder='templates')


@frontend.route('/')
def index():
    return render_template('index.html', publications=Publication.query.all())


@frontend.route('/organisations')
def organisations():
    return render_template('organisations.html', organisations=Organisation.query.all(), org_type='organisation')


@frontend.route('/<org_type>')
def organisation_by_type(org_type):
    query_filter = '%s%s'% (org_type, '%')
    orgs = Organisation.query.filter(Organisation.organisation.like(query_filter)).all()
    if not orgs:
        abort(404)
    return render_template('organisations.html', organisations=orgs, org_type=org_type)


@frontend.route('/organisations/<id>')
def organisation(id):
    org = Organisation.query.get(id)
    return render_template('organisation.html', organisation=org)


@frontend.route('/publications/<publication_id>')
def publication(publication_id):
    pub = Publication.query.get(publication_id)
    return render_template('publication.html', publication=pub)


@frontend.context_processor
def asset_path_context_processor():
    return {'asset_path': '/static/govuk_template'}
