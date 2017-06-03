from django.conf import settings

import logging.config
import yaml

conf = ''
with open(settings.LOG_CONF) as f:
    conf = yaml.load(f)
logging.config.dictConfig(conf)
