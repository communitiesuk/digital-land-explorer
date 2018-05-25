from flask import (
    Blueprint,
    render_template,
    abort,
    request)
from sqlalchemy import func

from application.frontend.forms import LatLongForm
from application.models import Organisation, Publication, Licence, Area, Attribution

frontend = Blueprint('frontend', __name__, template_folder='templates')


@frontend.route('/')
def index():
    form = LatLongForm()
    return render_template('index.html', form=form)


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
    points = org.other_areas.filter(func.ST_GeometryType(Area.geometry) == 'ST_Point').all()
    other_areas = org.other_areas.filter(func.ST_GeometryType(Area.geometry) != 'ST_Point')
    areas_by_type = {}
    for a in other_areas:
        area_type_key = a.data['properties']['area'].split(':')[0]
        if a.name is not None:
            a.data['properties']['content'] = a.name
        if area_type_key not in areas_by_type.keys():
            areas_by_type[area_type_key] = [a.data]
        else:
            areas_by_type[area_type_key].append(a.data)

    return render_template('organisation.html', organisation=org, points=points, areas_by_type=areas_by_type)


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
    a = Area.query.get(id)
    organisation = Organisation.query.filter_by(area=a).first()
    publication = Publication.query.filter(Publication.publication == a.area.split(':')[0]).first()
    return render_template('area.html',
                           area=a,
                           organisation=organisation,
                           publication=publication)


@frontend.route('/publication/<id>/areas')
def publication_area(id):
    if id[-1] == 's':
        prefix = id[:-1]
    else:
        prefix = id
    q = prefix + '%'
    publication = Publication.query.get(id)
    areas = [area.data for area in Area.query.filter(Area.area.like(q)).all()]
    return render_template('publication_area.html',
                           publication=publication,
                           areas=areas)


@frontend.route('/about-an-area')
def about_an_area():
    results = []
    message = None
    lat, long = request.args.get('latitude'), request.args.get('longitude')
    if lat is not None and long is not None:
        from application.extensions import db
        point = 'POINT(%f %f)' % (float(long), float(lat))
        areas = db.session.query(Area).filter(Area.geometry.ST_Contains(point))
        for area in areas:
            publication = Publication.query.filter(Publication.publication == area.area.split(':')[0]).first()
            organisation = Organisation.query.filter_by(area=area).first()
            results.append({'area': area, 'organisation': organisation, 'publication': publication})
        if not results:
            message = 'No results found'
    else:
        message = 'Both latitude and longitude parameters required'

    return render_template('about_an_area.html', latitude=lat, longitude=long, results=results, message=message)


@frontend.context_processor
def asset_path_context_processor():
    return {'asset_path': '/static/govuk_template'}
