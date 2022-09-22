import os
SECRET_KEY = os.urandom(32)
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

# Connect to the database
# TODO IMPLEMENT DATABASE URL
#postgresql://<user>:<pw>@<host>:<port>/<database_name>
SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:1234@localhost:5432/fine'

SQLALCHEMY_TRACK_MODIFICATIONS = False