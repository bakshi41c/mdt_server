import json
import log as logger

log = logger.get_logger('config.py')


def get_config():
    try:
        with open('config.json') as f:
            return json.load(f)
    except IOError as error:
        log.error('Error while reading config file')
        log.error(error)

    return {}

