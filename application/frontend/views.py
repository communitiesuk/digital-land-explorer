from flask import (
    Blueprint,
    render_template,
    request,
    jsonify
)

from sqlalchemy import func
from sqlalchemy.orm import load_only

from application.extensions import db
from application.frontend.forms import UKAreaForm
from application.models import Organisation, Publication, Licence, Feature, Copyright
from application.geocode import nom_geocode, nom_reverse_geocode

frontend = Blueprint('frontend', __name__, template_folder='templates')


@frontend.route('/')
def index():
    form = UKAreaForm()
    return render_template('index.html', form=form)


@frontend.route('/organisations')
def organisations():
    return render_template('organisations.html', organisations=Organisation.query.order_by("name").all())


@frontend.route('/organisations/<id>')
def organisation(id):
    org = Organisation.query.get(id)
    points = org.other_features.filter(func.ST_GeometryType(Feature.geometry) == 'ST_Point').all()
    other_features = org.other_features.filter(func.ST_GeometryType(Feature.geometry) != 'ST_Point')
    features_by_type = {}
    for f in other_features:
        feature_type_key = f.data['properties']['feature'].split(':')[0]
        if f.name is not None:
            f.data['properties']['content'] = f.name
        if feature_type_key not in features_by_type.keys():
            features_by_type[feature_type_key] = [f.data]
        else:
            features_by_type[feature_type_key].append(f.data)

    return render_template('organisation.html', organisation=org, points=points, features_by_type=features_by_type)


@frontend.route('/publications')
def publications():
    orgs = []
    for pub in Publication.query.all():
      if pub.organisation not in orgs:
        orgs.append(pub.organisation)
    return render_template('publications.html',
                            publications=Publication.query.all(),
                            org_num=len(orgs),
                            lic_num=len(Licence.query.all()))


@frontend.route('/publications/<id>')
def publication(id):
    pub = Publication.query.get(id)
    features = db.session.query(Feature).options(load_only('data')).filter(Feature.publication == pub.publication)
    features = [f.data for f in features]
    fs = {"type": "FeatureCollection", "features": features}
    return render_template('publication.html', publication=pub, features=fs)


@frontend.route('/publications/<id>/feature')
def publication_feature(id):
    swLng, swLat, neLng, neLat = [float(p) for p in request.args.get('bbox').split(',')]
    query = '''SELECT feature.data FROM feature WHERE feature.publication = '%s'
               AND feature.geometry && ST_MakeEnvelope(%f,%f,%f,%f, 4326);''' % (id, swLng, swLat, neLng, neLat)
    result = db.engine.execute(query)
    features = []
    for row in result:
        features.append(row[0])
    return jsonify(type="FeatureCollection", features=features), 200


@frontend.route('/licences')
def licences():
    return render_template('licences.html', licences=Licence.query.all())


@frontend.route('/licences/<id>')
def licence(id):
    lic = Licence.query.get(id)
    return render_template('licence.html', licence=lic)


@frontend.route('/attributions')
def attributions():
    return render_template('attributions.html', attributions=Copyright.query.all())


@frontend.route('/attributions/<id>')
def attribution(id):
    attr = Copyright.query.get(id)
    return render_template('attribution.html', attribution=attr)


@frontend.route('/feature/<id>')
def feature(id):
    f = db.session.query(Feature.data).filter(Feature.feature == id).first()
    publication = Publication.query.filter(Publication.publication == f.data['properties']['publication']).first()
    return render_template('feature.html',
                           feature=f.data,
                           organisation=publication.organisation,
                           publication=publication)


@frontend.route('/about-an-area')
def about_an_area():
    form = UKAreaForm()
    lat, lng = request.args.get('latitude'), request.args.get('longitude')
    return render_template('about_an_area.html', form=form, latitude=lat, longitude=lng)


@frontend.route('/about-an-area-query')
def about_an_area_query():
    results = []
    message = None
    lat, long, query = request.args.get('latitude'), request.args.get('longitude'), request.args.get('query')
    if lat is not None and long is not None:
        results, nearby = _get_data_from_a_point(lat, long)
        if not results:
            message = 'No results found'
    elif query is not None:
        geocoded_query = nom_geocode(query)
        if geocoded_query['success']:
            lat = geocoded_query['lat']
            long = geocoded_query['lng']
            results = _get_data_from_a_point(geocoded_query['lat'], geocoded_query['lng'])
        else:
            message = "Unable to geocode query: {}".format(query)
    else:
        message = 'Both latitude and longitude parameters required'

    return render_template('about_an_area_results.html', latitude=lat, longitude=long, results=results, nearby=nearby, message=message)


@frontend.route('/geocode', methods=['POST'])
def geocode():
  response = {}
  json = request.get_json()
  geocoded_query = nom_geocode(json['query'])
  return jsonify(geocoded_query)


@frontend.route('/reversegeocode', methods=['POST'])
def reverse_geocode():
  response = {}
  json = request.get_json()
  geocoded_query = nom_reverse_geocode(json['lat'], json['lng'])
  return jsonify(geocoded_query)


@frontend.context_processor
def asset_path_context_processor():
    return {'asset_path': '/static/govuk_template'}


def _get_data_from_a_point(lat, lng):
    results = []
    nearby = []
    from application.extensions import db
    point = func.ST_SetSRID(func.ST_MakePoint(float(lng), float(lat)), 4326)
    features = db.session.query(Feature.data,
                                Feature.feature,
                                Feature.publication).filter(Feature.geometry.ST_Contains(point)).all()

    for feature in features:
        publication = Publication.query.filter_by(publication=feature.publication).first()
        # organisation = Organisation.query.filter_by(feature_id=feature.feature).first()
        results.append({'feature': feature, 'organisation': publication.organisation, 'publication': publication})

    # from geoalchemy2 import Geography
    # from sqlalchemy import cast
    # nearby_features = db.session.query(Feature.data).filter(func.ST_DWithin(Feature.geometry, cast(point, Geography), 500)).all()
    # for feature in nearby_features:
    #     publication = Publication.query.filter_by(publication=feature.data['properties']['publication']).first()
    #     nearby.append({'feature': feature.data, 'organisation': publication.organisation, 'publication': publication})

    return results, nearby
