import json
import os
import boto3
import click
import requests
import csv
import platform

from urllib.request import urlopen
from contextlib import closing
from flask.cli import with_appcontext
from ijson import common
from application.models import Organisation, Feature, Publication, Licence, Copyright, organisation_feature
from application.extensions import db


if platform.system() == 'Darwin':
    from ijson.backends import yajl2 as ijson
else:
    import ijson


json_to_geo_query = "SELECT ST_AsText(ST_GeomFromGeoJSON('%s'))"
repo = os.getenv('DATA_REPO', 'https://raw.githubusercontent.com/communitiesuk/digital-land-collector')
branch = os.getenv('BRANCH', 'master')
s3_region = 'eu-west-2'
s3_bucket = 'digital-land'
s3_bucket_url = 'http://%s.s3.amazonaws.com' % s3_bucket


def floaten(event):
    if event[1] == 'number':
        return (event[0], event[1], float(event[2]))
    else:
        return event


def process_file(file_url):
    print('Processing', file_url)
    try:
        f = urlopen(file_url)
        events = map(floaten, ijson.parse(f))
        data = common.items(events, 'features.item')
        for feature in data:
            id = feature['properties'].get('feature')
            item = 'item:%s' % feature['properties'].get('item')
            publication = feature['properties'].get('publication')
            feature_id = id if id is not None else item
            if db.session.query(Feature).get(feature_id) is None:
                geo = json.dumps(feature['geometry'])
                geometry = db.session.execute(json_to_geo_query % geo).fetchone()[0]
                f = Feature(feature=feature_id, data=feature, geometry=geometry, item=item, publication=publication)
                db.session.add(f)
                db.session.commit()
        print('Done', file_url)
    except Exception as e:
        print(e)
        print('Error loading', file_url)


def _handle_markdown(item, contents):
    import frontmatter
    c = frontmatter.loads(contents)
    if item == 'licence':
        if not db.session.query(Licence).get(c.metadata['licence']):
            l = Licence(**c.metadata)
            db.session.add(l)
            db.session.commit()
            return 1
        else:
            print('licence', c.metadata['licence'], c.metadata['name'], 'already loaded')
            return 0
    elif item == 'copyright':
        if not db.session.query(Copyright).get(c.metadata['copyright']):
            c = Copyright(**c.metadata)
            db.session.add(c)
            db.session.commit()
            return 1
        else:
            print('copyright', c.metadata['copyright'], c.metadata['name'], 'already loaded')
            return 0

    elif item == 'publication':
        if not db.session.query(Publication).get(c.metadata['publication']):
            publication = Publication()
            publication.publication = c.metadata.get('publication')
            publication.name = c.metadata.get('name')
            publication.data_gov_uk = c.metadata.get('data-gov-uk')
            publication.data_url = c.metadata.get('data-url')
            publication.documentation_url = c.metadata.get('documentation-url')
            publication.organisation = Organisation.query.get(c.metadata.get('organisation')) if c.metadata.get('organisation') else None
            publication.licence = Licence.query.get(c.metadata.get('licence')) if c.metadata.get('licence') else None
            publication.copyright = Copyright.query.get(c.metadata.get('copyright')) if c.metadata.get('copyright') else None
            db.session.add(publication)
            db.session.commit()
            return 1
        else:
            print('publication', c.metadata['publication'], c.metadata['name'], 'already loaded')
            return 0


def _handle_organisation(contents):
    if not db.session.query(Organisation).get(contents['organisation']):
        organisation = Organisation(organisation=contents['organisation'],
                                    name=contents['name'],
                                    website=contents['website'])
        db.session.add(organisation)
        db.session.commit()
        return 1
    else:
        print('organisation', contents['organisation'], contents['name'], 'already loaded')
        return 0


def _load_features():
    s3 = boto3.resource('s3', region_name=s3_region)
    bucket = s3.Bucket(s3_bucket)
    for file in bucket.objects.all():
        file_url = '%s/%s' % (s3_bucket_url, file.key)
        process_file(file_url)


@click.command()
@with_appcontext
def load_everything():

    print('Loading the entire universe')

    items = ['licence', 'copyright', 'organisation', 'publication']
    count = 0

    for item in items:
        if item in ['licence', 'copyright', 'publication']:
            item_url = '%s/%s/data/%s/index.tsv' % (repo, branch, item)
            with closing(requests.get(item_url, stream=True)) as r:
                reader = csv.DictReader(r.iter_lines(decode_unicode=True), delimiter='\t')
                for row in reader:
                    file_url = '%s/%s/data/%s/%s' % (repo, branch, item, row['path'])
                    contents = requests.get(file_url).content.decode('utf-8')
                    count += _handle_markdown(item, contents)

        elif item == 'organisation':
            item_url = '%s/%s/data/organisation.tsv' % (repo, branch)
            with closing(requests.get(item_url, stream=True)) as r:
                reader = csv.DictReader(r.iter_lines(decode_unicode=True), delimiter='\t')
                for row in reader:
                    count += _handle_organisation(row)

        print('Loaded', count, item, 'files')
        count = 0

    _load_features()

    print('Done')


@click.command()
@with_appcontext
def clear_everything():
    from application.models import organisation_feature
    db.session.execute(organisation_feature.delete())
    db.session.query(Publication).delete()
    db.session.query(Organisation).delete()
    db.session.query(Feature).delete()
    db.session.query(Licence).delete()
    db.session.query(Copyright).delete()
    db.session.commit()
    print('cleared db')