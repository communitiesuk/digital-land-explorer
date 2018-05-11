import click
import requests
import csv

from contextlib import closing
from flask.cli import with_appcontext

from application.models import Organisation, Area
from application.extensions import db

@click.command()
@with_appcontext
def load_everything():

    areas_url = 'https://raw.githubusercontent.com/communitiesuk/digital-land-data/master/data/area/local-authority-district.geojson'
    data = requests.get(areas_url).json()

    try:
        for feature in data['features']:
            if feature.get('type') is not None and feature.get('type') == 'Feature':
                area_id = feature['properties']['area']
                area = Area(area=area_id, data=feature)
                db.session.add(area)

        orgs_url = 'https://raw.githubusercontent.com/communitiesuk/digital-land-data/master/data/organisation.tsv'
        with closing(requests.get(orgs_url, stream=True)) as r:
            reader = csv.DictReader(r.iter_lines(decode_unicode=True), delimiter='\t')
            for row in reader:
                org = Organisation(organisation=row['organisation'],
                                   name=row['name'],
                                   website=row['website'])

                if row.get('area'):
                    area = db.session.query(Area).get(row.get('area'))
                    org.area = area

                db.session.add(org)

        db.session.commit()

    except:

        db.session.rollback()


@click.command()
@with_appcontext
def clear_everything():
    db.session.query(Organisation).delete()
    db.session.query(Area).delete()
    db.session.commit()