import argparse
import asyncio
import logging
import os
import re
import sys
import signal
import functools
import traceback

import yaml

from pywalkgen.health import HealthServer
from pywalkgen.walkgen import WalkPatternGenerator
from pywalkgen.in_mem_db import RedisDB

logging.basicConfig(level=logging.WARNING, format='%(levelname)-8s [%(filename)s:%(lineno)d] %(message)s')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler('/tmp/walkgen.log')
handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(levelname)-8s-[%(filename)s:%(lineno)d]-%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

is_sighup_received = False

# YAML configuration to read Environment Variables in Configuration File
env_pattern = re.compile(r".*?\${(.*?)}.*?")


def env_constructor(loader, node):
    value = loader.construct_scalar(node)
    for group in env_pattern.findall(value):
        value = value.replace(f"${{{group}}}", os.environ.get(group))
    return value


yaml.add_implicit_resolver("!pathex", env_pattern)
yaml.add_constructor("!pathex", env_constructor)


def parse_arguments():
    """Arguments to run the script"""
    parser = argparse.ArgumentParser(description='Walk Generator')
    parser.add_argument('--config', '-c', required=True, help='YAML Configuration File for Walk Generator with path')
    return parser.parse_args()


def signal_handler(name):
    global is_sighup_received
    is_sighup_received = True


async def app(eventloop, config):
    """Main application for Personnel Generator"""
    walkers_in_map = []
    global is_sighup_received

    while True:

        # Read configuration
        try:
            walk_config = read_config(yaml_file=config, rootkey='walk_generator')
        except Exception as e:
            logger.error(f'Error while reading configuration: {e}')
            break

        logger.debug("Personnel Generator Version: %s", walk_config['version'])

        # health server
        # health_server = HealthServer(config=walk_config["health_server"], event_loop=eventloop)
        # eventloop.create_task(health_server.server_loop())

        try:
            redis_db = RedisDB(host=walk_config["in_mem_db"]["server"]["address"],
                               port=walk_config["in_mem_db"]["server"]["port"],
                               password=walk_config["in_mem_db"]["credentials"]["password"])
        except Exception as e:
            logger.error(f'Error while setting-up or connecting Redis Client : {e}')
            break

        try:
            sample_interval = walk_config["sample_interval"]
            assert type(sample_interval) is int or type(sample_interval) is float
        except Exception as e:
            logger.error(f'Sample interval must be number. Check config file : {e}')
            break

        # Personnel instantiation
        for each_walker in walk_config["personnels"]:
            # check for protocol key
            if "protocol" not in each_walker:
                logger.critical("no 'protocol' key found.")
                sys.exit(-1)

            # create walker
            walker = WalkPatternGenerator(eventloop=eventloop, config_file=each_walker, db=redis_db)
            await walker.connect()
            walkers_in_map.append(walker)

        # continuously monitor signal handle and update walker
        while not is_sighup_received:
            for each_walker in walkers_in_map:
                await each_walker.update()

            if sample_interval >= 0:
                await asyncio.sleep(delay=sample_interval)
            else:
                await asyncio.sleep(delay=0)

        # If SIGHUP Occurs, Delete the instances
        for entry in walkers_in_map:
            del entry

        # reset sighup handler flag
        is_sighup_received = False


def read_config(yaml_file, rootkey):
    """Parse the given Configuration File"""
    if os.path.exists(yaml_file):
        with open(yaml_file, 'r') as config_file:
            yaml_as_dict = yaml.load(config_file, Loader=yaml.FullLoader)
        return yaml_as_dict[rootkey]
    else:
        raise FileNotFoundError
        logger.error('YAML Configuration File not Found.')


def app_main():
    """Initialization"""
    args = parse_arguments()
    if not os.path.isfile(args.config):
        logger.error("configuration file not readable. Check path to configuration file")
        sys.exit(-1)

    event_loop = asyncio.get_event_loop()
    event_loop.add_signal_handler(signal.SIGHUP, functools.partial(signal_handler, name='SIGHUP'))
    event_loop.run_until_complete(app(event_loop, args.config))
