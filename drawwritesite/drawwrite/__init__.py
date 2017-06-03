import logging.config
import yaml

conf = ''
with open('logconf.yaml') as f:
    conf = yaml.load(f)
logging.config.dictConfig(conf)
