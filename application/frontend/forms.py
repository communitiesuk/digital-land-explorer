from flask_wtf import FlaskForm
from wtforms import FloatField, StringField
from wtforms.validators import DataRequired


class LatLongForm(FlaskForm):

    latitude = FloatField('Latitude', validators=[DataRequired()])
    longitude = FloatField('Longitude', validators=[DataRequired()])

class UKAreaForm(FlaskForm):
    query = StringField('Enter UK location or click on map', validators=[DataRequired()])