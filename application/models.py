from geoalchemy2 import Geometry
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSON

from application.extensions import  db


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


class Attribution(db.Model):
    attribution = db.Column(db.String(64), primary_key=True)
    name = db.Column(db.String(256))
    url = db.Column(db.Text)

    publications = db.relationship('Publication', backref='attribution', lazy=True)


class Organisation(db.Model):
    organisation = db.Column(db.String(64), primary_key=True)    # government-organisation:D6
    name = db.Column(db.String(256))
    website = db.Column(db.String(256))
    text = db.Column(db.Text)
    area_id = db.Column(db.String(256), ForeignKey('area.area', name='organisation_area_fkey'))
    area = db.relationship('Area', uselist=False)

    category_id = db.Column(db.String(64), ForeignKey('category.category', name='organisation_category_fkey'))
    publications = db.relationship('Publication', backref='organisation', lazy=True)

    def feature(self):
        if self.area is not None:
            return self.area.data
        return {}


class Publication(db.Model):
    """
    documents published by an organisation
    """
    publication = db.Column(db.String(64), primary_key=True)
    name = db.Column(db.String(256))

    organisation_id = db.Column(db.String(64), ForeignKey('organisation.organisation',
                                                          name='publication_organisation_fkey'))

    licence_id = db.Column(db.String(256), ForeignKey('licence.licence', name='publication_licence_fkey'))

    attribution_id = db.Column(db.String(64), ForeignKey('attribution.attribution',
                                                          name='publication_attribution_fkey'))

    category_id = db.Column(db.String(64), ForeignKey('category.category', name='publication_category_fkey'))

    url = db.Column(db.Text)  # check for url field type in postgres
    data_url =  db.Column(db.Text)  # check for url field type in postgres

    # editions = relationship('Edition', backref='publication', lazy=True)
    # task = db.ForeignKey(Task) # how to fetch an edition ..


class Area(db.Model):
    area = db.Column(db.String(256), primary_key=True)
    data = db.Column(JSON)
    geometry = db.Column(Geometry())

# class Edition(db.Model):
#     """
#     instance of a publication
#     """
#     publication_id = db.Column(db.String(64), ForeignKey('publication.publication', name='publication_id_edition_fkey'))
#     publication = relationship('Publication', back_populates='publication')
#
#     collected = db.Column(db.DateTime())
#
#     __table_args__ = (
#         PrimaryKeyConstraint(publication_id, collected, name='publication_id_collected_pkey'), {}
#     )


# class Dataset(Publication):
#     """
#     a register or pseudo register built from a publication for our domain ..
#     """
#     dataset = db.Column(db.String(64), primary_key=True)


# class Datatype(db.Model):
#     datatype = db.Column(db.String(64), primary_key=True)
#     text = db.Column(db.Text)
#
#
# class Field(db.Model):
#     field = db.Column(db.String(64), primary_key=True)
#     text = db.Column(db.Text)
#     datatype = db.ForeignKey(Datatype)
#
#
# class Value(db.Model):
#     field = db.ForeignKey(Field)
#     value = db.TextField()          # contents depending on datatype
#
#
# class Item(db.Model):
#     dataset = db.ForeignKey(Dataset)
#     values = db.ManyToMany(Value)