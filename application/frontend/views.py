from flask import (
    Blueprint,
    render_template,
    abort
)

from sqlalchemy import func

from application.frontend.forms import LatLongForm
from application.models import Organisation, Publication, Licence, Area, Attribution

frontend = Blueprint('frontend', __name__, template_folder='templates')


@frontend.route('/')
def index():
    from application.extensions import db
    area_count = db.session.query(Area.area).count()
    return render_template('index.html',
                           publications=Publication.query.all(),
                           licences=Licence.query.all(),
                           organisations=Organisation.query.all(),
                           area_count=area_count)


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


@frontend.route('/publications')
def publications():
    return render_template('publications.html', publications=Publication.query.all())


@frontend.route('/publications/<id>')
def publication(id):
    pub = Publication.query.get(id)
    return render_template('publication.html', publication=pub)


@frontend.route('/licences')
def licences():
    return render_template('licences.html', licences=Licence.query.all())


@frontend.route('/licences/<id>')
def licence(id):
    lic = Licence.query.get(id)
    return render_template('licence.html', licence=lic)


@frontend.route('/attributions')
def attributions():
    return render_template('attributions.html', attributions=Attribution.query.all())


@frontend.route('/attributions/<id>')
def attribution(id):
    attr = Attribution.query.get(id)
    return render_template('attribution.html', attribution=attr)


@frontend.route('/areas')
def areas():
    return render_template('areas.html', count=1000)


@frontend.route('/areas/<id>')
def area(id):
    from flask import request
    a = Area.query.get(id)
    organisation = Organisation.query.filter_by(area=a).first()
    return render_template('area.html',
                           area=a,
                           lat=request.args.get('lat'),
                           long=request.args.get('long'),
                           organisation=organisation)


@frontend.route('/geoquery', methods=['GET', 'POST'])
def geoquery():

    form = LatLongForm()
    results = []
    message = None

    if form.validate_on_submit():
        from application.extensions import db
        point = 'POINT(%f %f)' % (form.longitude.data, form.latitude.data)
        areas = db.session.query(Area).filter(Area.geometry.ST_Contains(point))
        for area in areas:
            organisation = Organisation.query.filter_by(area=area).first()
            results.append({'area': area, 'organisation': organisation})
        if not results:
            message = 'No results found'

    return render_template('geoquery.html', form=form, results=results, message=message)


@frontend.context_processor
def asset_path_context_processor():
    return {'asset_path': '/static/govuk_template'}
