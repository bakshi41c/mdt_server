import logging


def get_logger(log_name):
    logger = logging.getLogger(log_name)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # # create a file handler
    # file_handler = logging.FileHandler(log_name + '.log')
    # file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # add the handlers to the logger
    # logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
