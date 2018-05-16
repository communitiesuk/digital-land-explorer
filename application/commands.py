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
            try:
                db.session.add(lic)
                db.session.commit()
                count += 1
            except Exception as e:
                print(e)
                db.session.rollback()

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
            try:
                db.session.add(attribution)
                db.session.commit()
                count += 1
            except Exception as e:
                print(e)
                db.session.rollback()

    print('Loaded', count, 'attributions')
    count = 0

    areas = 'https://raw.githubusercontent.com/communitiesuk/digital-land-data/master/data/area/index.tsv'
    with closing(requests.get(areas, stream=True)) as r:
        reader = csv.DictReader(r.iter_lines(decode_unicode=True), delimiter='\t')
        for row in reader:
            area_url = 'https://raw.githubusercontent.com/communitiesuk/digital-land-data/master/data/area/%s' % row['path']
            area_data = requests.get(area_url).json()
            for feature in area_data['features']:
                if feature.get('type') is not None \
                        and feature.get('type') == 'Feature'\
                        and feature.get('properties').get('area') is not None:
                    area_id = feature['properties']['area']
                    area = Area(area=area_id, data=feature)
                    try:
                        db.session.add(area)
                        db.session.commit()
                        count += 1
                    except Exception as e:
                        print(e)
                        db.session.rollback()

    print('Loaded', count, 'areas')
    count = 0

    organisations = 'https://raw.githubusercontent.com/communitiesuk/digital-land-data/master/data/organisation.tsv'
    with closing(requests.get(organisations, stream=True)) as r:
        reader = csv.DictReader(r.iter_lines(decode_unicode=True), delimiter='\t')
        for row in reader:
            org = Organisation(organisation=row['organisation'],
                               name=row['name'],
                               website=row['website'])
            if row.get('area'):
                area = db.session.query(Area).get(row.get('area'))
                org.area = area
            try:
                db.session.add(org)
                db.session.commit()
                count += 1
            except Exception as e:
                print(e)
                db.session.rollback()

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
            publication = Publication(publication=md.Meta['publication'][0],
                                      name=md.Meta['name'][0],
                                      url=md.Meta['documentation-url'][0],
                                      data_url=md.Meta['data-url'][0])

            organisation = db.session.query(Organisation).get(md.Meta['organisation'][0])
            if organisation is not None:
                publication.organisation = organisation

            lic = db.session.query(Licence).get(md.Meta['licence'][0])
            if lic is not None:
                publication.licence = lic

            attribution = db.session.query(Attribution).get(md.Meta['copyright'][0])
            if attribution is not None:
                publication.attribution = attribution

            try:
                db.session.add(publication)
                db.session.commit()
                count += 1
            except Exception as e:
                print(e)
                db.session.rollback()

    print('Loaded', count, 'publications')

    # TODO geography. the body text as well?


@click.command()
@with_appcontext
def clear_everything():
    db.session.query(Publication).delete()
    db.session.query(Organisation).delete()
    db.session.query(Area).delete()
    db.session.query(Licence).delete()
    db.session.query(Attribution).delete()
    db.session.commit()
    print('cleared db')