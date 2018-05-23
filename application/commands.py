import json

import click
import markdown
import requests
import csv

from contextlib import closing
from flask.cli import with_appcontext

from application.models import Organisation, Area, Publication, Licence, Attribution
from application.extensions import db


@click.command()
@with_appcontext
def load_everything():

    print('Loading the entire universe')

    count = 0
    licenses = 'https://raw.githubusercontent.com/communitiesuk/digital-land-data/master/data/licence.tsv'
    with closing(requests.get(licenses, stream=True)) as r:
        reader = csv.DictReader(r.iter_lines(decode_unicode=True), delimiter='\t')
        for row in reader:
            lic = Licence(licence=row['licence'],
                          name=row['name'],
                          url=row['url'])
            db.session.add(lic)
            db.session.commit()
            count += 1

    print('Loaded', count, 'licences')
    count = 0

    attributions = 'https://raw.githubusercontent.com/communitiesuk/digital-land-data/master/data/copyright/index.tsv'
    with closing(requests.get(attributions, stream=True)) as r:
        reader = csv.DictReader(r.iter_lines(decode_unicode=True), delimiter='\t')
        for row in reader:
            attribution_url = 'https://raw.githubusercontent.com/communitiesuk/digital-land-data/master/data/copyright/%s' % row['path']
            attribution_data = requests.get(attribution_url).content.decode('utf-8')
            md = markdown.Markdown(extensions=['markdown.extensions.meta'])
            md.convert(attribution_data)
            attribution = Attribution(attribution=md.Meta['copyright'][0],
                                      name=md.Meta['name'][0])
            count += 1

    print('Loaded', count, 'attributions')
    count = 0

    prefix_file = 'https://raw.githubusercontent.com/communitiesuk/digital-land-data/master/data/prefix.tsv'
    prefixes = {}
    org_area_mappings = []
    with closing(requests.get(prefix_file, stream=True)) as r:
        reader = csv.DictReader(r.iter_lines(decode_unicode=True), delimiter='\t')
        for row in reader:
            prefixes[row.get('prefix')] = row.get('organisation')

    print('Load data for areas')
    data = 'https://raw.githubusercontent.com/communitiesuk/digital-land-data/master/data/data/index.tsv'
    area_data_mappings = {}
    with closing(requests.get(data, stream=True)) as r:
        reader = csv.DictReader(r.iter_lines(decode_unicode=True), delimiter='\t')
        for row in reader:
            data_url = 'https://raw.githubusercontent.com/communitiesuk/digital-land-data/master/data/data/%s' % row[
                'path']
            with closing(requests.get(data_url, stream=True)) as data_r:
                data_reader = csv.DictReader(data_r.iter_lines(decode_unicode=True), delimiter='\t')
                for data_row in data_reader:
                    area_data_mappings[data_row.get('area')] = data_row.get('name')

    areas = 'https://raw.githubusercontent.com/communitiesuk/digital-land-data/master/data/area/index.tsv'
    json_to_geo_query = "SELECT ST_AsText(ST_GeomFromGeoJSON('%s'))"
    with closing(requests.get(areas, stream=True)) as r:
        reader = csv.DictReader(r.iter_lines(decode_unicode=True), delimiter='\t')
        for row in reader:
            print('Loading', row['path'])
            area_url = 'https://raw.githubusercontent.com/communitiesuk/digital-land-data/master/data/area/%s' % row['path']
            area_data = requests.get(area_url).json()
            for feature in area_data['features']:
                if feature.get('type') is not None \
                        and feature.get('type') == 'Feature'\
                        and feature.get('properties').get('area') is not None:
                    area_id = feature['properties']['area']
                    geo = json.dumps(feature.get('geometry'))
                    geometry = db.session.execute(json_to_geo_query % geo).fetchone()[0]
                    area = Area(area=area_id, data=feature, geometry=geometry)
                    if area_id in area_data_mappings.keys():
                        area.name = area_data_mappings[area_id]

                    db.session.add(area)
                    db.session.commit()
                    count += 1
                    p = area_id.split(':')[0]
                    if p in prefixes.keys():
                        org = prefixes.get(p)
                        org_area_mappings.append({'organisation': org, 'area': area_id})

    print('Loaded', count, 'areas')
    count = 0

    organisations = 'https://raw.githubusercontent.com/communitiesuk/digital-land-data/master/data/organisation.tsv'
    with closing(requests.get(organisations, stream=True)) as r:
        reader = csv.DictReader(r.iter_lines(decode_unicode=True), delimiter='\t')
        for row in reader:
            org = Organisation(organisation=row.get('organisation'),
                               name=row.get('name'),
                               website=row.get('website'))
            if row.get('area'):
                area = db.session.query(Area).get(row.get('area'))
                org.area = area

            db.session.add(org)
            db.session.commit()
            count += 1

    print('Loaded', count, 'organisations')
    count = 0

    publications = 'https://raw.githubusercontent.com/communitiesuk/digital-land-data/master/data/publication/index.tsv'
    with closing(requests.get(publications, stream=True)) as r:
        reader = csv.DictReader(r.iter_lines(decode_unicode=True), delimiter='\t')
        for row in reader:
            publication_url = 'https://raw.githubusercontent.com/communitiesuk/digital-land-data/master/data/publication/%s' % row['path']
            publication_data = requests.get(publication_url).content.decode('utf-8')
            md = markdown.Markdown(extensions=['markdown.extensions.meta'])
            md.convert(publication_data)
            pub = md.Meta['publication'][0]
            name = md.Meta['name'][0]
            url = md.Meta.get('documentation-url')
            url = url[0] if url else None
            data_url=md.Meta['data-url'][0]

            publication = Publication(publication=pub,
                                      name=name,
                                      url=url,
                                      data_url=data_url)

            organisation = db.session.query(Organisation).get(md.Meta['organisation'][0])
            if organisation is not None:
                publication.organisation = organisation

            lic = db.session.query(Licence).get(md.Meta['licence'][0])
            if lic is not None:
                publication.licence = lic

            attribution = db.session.query(Attribution).get(md.Meta['copyright'][0])
            if attribution is not None:
                publication.attribution = attribution

            db.session.add(publication)
            db.session.commit()
            count += 1

    print('Loaded', count, 'publications')

    from application.models import organisation_area

    for org_area in org_area_mappings:
        # don't load for ons at the moment before introducing some more
        # thinking about how to load many areas for org.
        if org_area['organisation'] != 'government-organisation:D303':
            db.session.execute(organisation_area.insert().values(**org_area))
            db.session.commit()

    print('Loaded other areas for organisations')
    print('Done')


@click.command()
@with_appcontext
def clear_everything():
    from application.models import organisation_area
    db.session.execute(organisation_area.delete())
    db.session.query(Publication).delete()
    db.session.query(Organisation).delete()
    db.session.query(Area).delete()
    db.session.query(Licence).delete()
    db.session.query(Attribution).delete()
    db.session.commit()
    print('cleared db')