import json
import log as logger
import os

log = logger.get_logger('config.py')


def get_config():
    filename = os.getenv('MDT_SERVER_CONFIG', 'config') + '.json'
    log.debug("Using config file " + filename)
    try:
        with open(filename) as f:
            return json.load(f)
    except IOError as error:
        log.error('Error while reading config file')
        log.error(error)

    return {}


def get_test_config():
    try:
        with open('tests/test_config.json') as f:
            return json.load(f)
    except IOError as error:
        log.error('Error while reading config file')
        log.error(error)

    return {}

