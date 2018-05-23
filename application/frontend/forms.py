from flask_wtf import FlaskForm
from wtforms import FloatField, StringField
from wtforms.validators import DataRequired


class LatLongForm(FlaskForm):

    latitude = FloatField('Latitude', validators=[DataRequired()])
    longitude = FloatField('Longitude', validators=[DataRequired()])

class UKAreaForm(FlaskForm):
    location = StringField('UK location', validators=[DataRequired()])
