import sys
import logging
import yaml
import datetime
import os
from os.path import join as pjoin


def setup_logger(logdir, name='log', level=logging.INFO):
    # define a naming prefix
    date = datetime.datetime.now().strftime("%Y%m%d")
    prefix = f'{name}_{date}'

    # find all logs with the same prefix
    logs = os.listdir(logdir)
    logs = [l for l in logs if l.startswith(prefix)]

    # find the next available number
    path_to_log = pjoin(logdir, f'{name}_{date}_{len(logs):04}.log')

    # setup the logger
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s-%(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(path_to_log),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.info(f"Logging to {path_to_log}")


def get_global_config():
    with open('global.cfg', 'r') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return config


def timing_decorator(func, *args, **kwargs):
    def wrapper(*args, **kwargs):
        logging.info(f"Running {func.__name__}...")
        t0 = datetime.datetime.now()
        out = func(*args, **kwargs)
        dt = (datetime.datetime.now() - t0).total_seconds()
        logging.info(
            f"Done running {func.__name__}. "
            f"Time elapsed: {int(dt//60)}m{int(dt%60)}s.")
        return out
    return wrapper