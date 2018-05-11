===============================
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

Make a virtualenv for the project and install python dependencies

    pip install -r requirements.txt

Create database schema

    flask db upgrade



Run the application

    flask run


Note you can add and commit public environment variables to .flaskenv, do not add anything secret to this
file.


Deployment
----------

In your production environment, make sure the ``FLASK_CONFIG`` environment variable is set to ``config.Config``.

