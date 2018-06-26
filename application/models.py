from geoalchemy2 import Geometry
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSON, JSONB

from application.extensions import  db


organisation_feature = db.Table('organisation_feature',
                                db.Column('organisation', db.String(64), db.ForeignKey('organisation.organisation'),
                                          primary_key=True),
                                db.Column('feature', db.String(256), db.ForeignKey('feature.feature'),
                                          primary_key=True),
                                )

class Category(db.Model):
    """
    actually our wiki, containing concepts and tags, linked to by markdown
    """
    category = db.Column(db.String(64), primary_key=True)        # Local Authority, Planning Authority, etc
    text = db.Column(db.Text)

    publications = db.relationship('Publication', backref='category', lazy=True)
    organisations  = db.relationship('Organisation', backref='category', lazy=True)


class Licence(db.Model):
    licence = db.Column(db.String(256), primary_key=True)
    name = db.Column(db.String(256))
    url = db.Column(db.Text)
    text = db.Column(db.Text)

    publications = db.relationship('Publication', backref='licence', lazy=True)


class Copyright(db.Model):
    copyright = db.Column(db.String(64), primary_key=True)
    name = db.Column(db.String(256))
    url = db.Column(db.Text)

    publications = db.relationship('Publication', backref='copyright', lazy=True)


class Organisation(db.Model):
    organisation = db.Column(db.String(64), primary_key=True)    # government-organisation:D6
    name = db.Column(db.String(256))
    website = db.Column(db.String(256))
    text = db.Column(db.Text)
    feature_id = db.Column(db.String(256), ForeignKey('feature.feature', name='organisation_feature_fkey'))
    feature = db.relationship('Feature', uselist=False)

    category_id = db.Column(db.String(64), ForeignKey('category.category', name='organisation_category_fkey'))
    publications = db.relationship('Publication', backref='organisation', lazy=True)

    other_features = db.relationship('Feature',
                                     lazy='dynamic',
                                     secondary=organisation_feature,
                                     primaryjoin='Organisation.organisation == organisation_feature.columns.organisation',
                                     secondaryjoin='Feature.feature == organisation_feature.columns.feature',
                                     backref=db.backref('organisation', lazy=True))

class Publication(db.Model):
    """
    documents published by an organisation
    """
    publication = db.Column(db.String(64), primary_key=True)
    name = db.Column(db.String(256))

    organisation_id = db.Column(db.String(64), ForeignKey('organisation.organisation',
                                                          name='publication_organisation_fkey'))

    licence_id = db.Column(db.String(256), ForeignKey('licence.licence', name='publication_licence_fkey'))

    copyright_id = db.Column(db.String(64), ForeignKey('copyright.copyright',
                                                          name='publication_copyright_fkey'))

    category_id = db.Column(db.String(64), ForeignKey('category.category', name='publication_category_fkey'))

    data_url = db.Column(db.Text)
    data_gov_uk = db.Column(db.Text)
    documentation_url = db.Column(db.Text)

    # editions = relationship('Edition', backref='publication', lazy=True)
    # task = db.ForeignKey(Task) # how to fetch an edition ..


class Feature(db.Model):
    feature = db.Column(db.String(256), primary_key=True)
    item = db.Column(db.String(256))
    data = db.Column(JSONB)
    geometry = db.Column(Geometry(srid=4326))
    name = db.Column(db.Text)
    publication = db.Column(db.String(64))

