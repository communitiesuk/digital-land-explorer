# -*- coding: utf-8 -*-
"""Extensions module. Each extension is initialized in the app factory located
in factory.py
"""

from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

from flask_compress import Compress
compress = Compress()

from flask_caching import Cache
cache = Cache(config={'CACHE_TYPE': 'simple'})