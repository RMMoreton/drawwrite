"""A Django module implementing the DrawWrite game."""

import logging.config

from django.conf import settings
import yaml

def configure_logging():
    """Configure logging for this module."""
    conf = ''
    with open(settings.LOG_CONF) as conf_file:
        conf = yaml.load(conf_file)
    try:
        logging.config.dictConfig(conf)
    except ValueError as error:
        print(error)

if __name__ == '__main__':
    configure_logging()
