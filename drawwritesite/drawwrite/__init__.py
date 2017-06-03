from django.conf import settings

import logging.config
import yaml

conf = ''
with open(settings.LOG_CONF) as f:
    conf = yaml.load(f)
try:
    logging.config.dictConfig(conf)
except ValueError as e:
    print(e)
