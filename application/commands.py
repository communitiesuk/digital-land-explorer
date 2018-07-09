import json
import os
import boto3
import click
import requests
import csv
import platform

from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import urlopen
from contextlib import closing
from flask.cli import with_appcontext
from ijson import common
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from application.models import Organisation, Feature, Publication, Licence, Copyright, organisation_feature
from application.extensions import db


if platform.system() == 'Darwin':
    from ijson.backends import yajl2 as ijson
else:
    import ijson


json_to_geo_query = "SELECT ST_SetSRID(ST_GeomFromGeoJSON('%s'), 4326);"


def floaten(event):
    if event[1] == 'number':
        return (event[0], event[1], float(event[2]))
    else:
        return event


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


def _handle_organisation(contents, org_feature_mappings):
    if contents.get('feature'):
        org_feature_mappings[contents.get('feature')] = contents['organisation']
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


@click.command()
@with_appcontext
def load_everything():

    from flask import current_app

    s3_region = current_app.config.S3_REGION
    s3_bucket = current_app.config.S3_BUCKET
    s3_bucket_url = 'http://%s.s3.amazonaws.com' % s3_bucket

    print('Loading the entire universe')

    org_feature_mappings = {}

    items = ['licence', 'copyright', 'organisation', 'publication']
    count = 0

    for item in items:
        if item in ['licence', 'copyright', 'publication']:
            item_url = '%s/%s/index.tsv' % (s3_bucket_url, item)
            print('Loading', item_url)
            with closing(requests.get(item_url, stream=True)) as r:
                reader = csv.DictReader(r.iter_lines(decode_unicode=True), delimiter='\t')
                for row in reader:
                    file_url = '%s/%s/%s' % (s3_bucket_url, item, row['path'])
                    print('Processing', file_url)
                    contents = requests.get(file_url).content.decode('utf-8')
                    count += _handle_markdown(item, contents)

        elif item == 'organisation':
            item_url = '%s/organisation.tsv' % s3_bucket_url
            print('Loading', item_url)
            with closing(requests.get(item_url, stream=True)) as r:
                reader = csv.DictReader(r.iter_lines(decode_unicode=True), delimiter='\t')
                for row in reader:
                    count += _handle_organisation(row, org_feature_mappings)

        print('Loaded', count, item, 'files')
        count = 0

    try:
        _load_features(org_feature_mappings, s3_bucket, s3_region)
    finally:
        db.session.execute('CLUSTER feature USING idx_feature_geometry')
        # db.session.execute('VACUUM ANALYZE feature;')

    print('Done')


def _load_features(org_feature_mappings, s3_bucket, s3_region):

    s3_bucket_url = 'http://%s.s3.amazonaws.com' % s3_bucket
    s3 = boto3.resource('s3', region_name=s3_region)
    bucket = s3.Bucket(s3_bucket)
    urls = ['%s/%s' % (s3_bucket_url, file.key) for file in bucket.objects.filter(Prefix='feature')]

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_file, url, org_feature_mappings) for url in urls]
        for future in as_completed(futures):
            print(future.result())


@click.command()
@click.option('--file')
@with_appcontext
def load_local_file(file):
    process_file(file, {})


def process_file(file_url, org_feature_mappings):
    print('Loading', file_url)
    some_engine = create_engine(os.getenv('SQLALCHEMY_DATABASE_URI', 'postgresql://localhost/digital_land'))
    Session = sessionmaker(bind=some_engine)
    session = Session()
    total = 0
    try:
        if file_url.startswith('http'):
            f = urlopen(file_url)
        else:
            f = open(file_url, 'rb')
        events = map(floaten, ijson.parse(f))
        data = common.items(events, 'features.item')
        records = []
        orgs_to_save = []
        processed = set([])

        for feature in data:
            id = feature['properties'].get('feature')
            item = 'item:%s' % feature['properties'].get('item')
            publication = feature['properties'].get('publication')
            feature_id = id if id is not None else item

            if session.query(Feature).get(feature_id) is None and feature_id not in processed:
                geo = json.dumps(feature['geometry'])
                geometry = session.execute(json_to_geo_query % geo).fetchone()[0]

                if feature_id in org_feature_mappings:
                    org = session.query(Organisation).get(org_feature_mappings[feature_id])
                    org.feature_id = feature_id
                    orgs_to_save.append(org)

                records.append(dict(feature=feature_id,
                                    data=feature,
                                    geometry=geometry,
                                    item=item,
                                    publication=publication))

                processed.add(feature_id)

                if len(records) % 10000 == 0:
                    session.bulk_insert_mappings(Feature, records)
                    session.bulk_save_objects(orgs_to_save)
                    session.commit()
                    print('Saved', len(records), 'features from', file_url)
                    total += len(records)
                    records = []
                    orgs_to_save = []

        session.bulk_insert_mappings(Feature, records)
        session.bulk_save_objects(orgs_to_save)
        session.commit()

        print('Saved', len(records), 'features from', file_url)
        total += len(records)
        print('Finished loading', file_url)

    except Exception as e:
        print(e)
        print('Error loading', file_url)
    finally:
        try:
            f.close()
        except:
            pass

    return 'Loaded total of %d features from %s' % (total, file_url)


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