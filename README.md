digital-land-explorer
===============================

Website to find and explore digital land data


Requirements

- [Python 3](https://www.python.org/)
- [Node](https://nodejs.org/en/) and [Npm](https://www.npmjs.com/)
- [Postgres](https://www.postgresql.org/)

Quickstart
----------

Install front end build tool (gulp)

    npm install && gulp scss


Create a local postgres database for the application called **digital_land** (see the .flaskenv file)

If you installed postgres with Homebrew, create db with:

    createdb digital_land

Install PostGIS

If you're using Postgres.app on OSX it should be installed already but you'll need to add it to the digital_land db. Using `psql -d digital_land`, run:

    CREATE EXTENSION postgis;

Check if all went well

    SELECT PostGIS_Version();

You should see something similar to:

    2.4 USE_GEOS=1 USE_PROJ=1 USE_STATS=1

Create a .env (note .env file is git ignored) and add MAPBOX_TOKEN to you .env file. To get token create an account at
[Mapbox](https://www.mapbox.com/)

Make a virtualenv for the project and install python dependencies

    pip install -r requirements.txt

Run database migrations

    flask db upgrade

Load data

    flask load

Run the application

    flask run

Note you can add and commit public environment variables to .flaskenv, do not add anything secret to this
file.

Other useful commands
---------------------

Create database schema

    flask db upgrade

Clear data for reload

    flask clear

Create a new database migration

    flask run migrate

Deployment
----------

In your production environment, make sure the ``FLASK_CONFIG`` environment variable is set to ``config.Config``.

