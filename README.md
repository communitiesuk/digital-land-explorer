digital-land-explorer
===============================

Website to find and explore digital land data


Requirements

- [Python 3](https://www.python.org/)
- [Node](https://nodejs.org/en/) and [Npm](https://www.npmjs.com/)

Quickstart
----------

Install front end build tool (gulp)

    npm install && gulp scss


Create a local postgres database for the application called digital_land (see the .flaskenv file)

Create a .env (note .env file is git ignored) and add MAPBOX_TOKEN to you .env file. To get token create an account at
[Mapbox](https://www.mapbox.com/)

Make a virtualenv for the project and install python dependencies

    pip install -r requirements.txt

Create database schema

    flask db upgrade


Run database migrations

    flask db upgrade

Load data

    flask load

Clear data for reload

    flask clear


Run the application

    flask run


Create a new database migration

    flask run migrate


Note you can add and commit public environment variables to .flaskenv, do not add anything secret to this
file.


Deployment
----------

In your production environment, make sure the ``FLASK_CONFIG`` environment variable is set to ``config.Config``.

