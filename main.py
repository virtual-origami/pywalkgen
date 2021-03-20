import argparse
import asyncio
import logging
import os
import sys
import signal
import functools
from WalkGen.WalkGenerator import WalkPatternGenerator

logging.basicConfig( level=logging.WARNING, format='%(levelname)-8s [%(filename)s:%(lineno)d] %(message)s' )
sighup_handler_var = False


def parse_arguments():
    """Arguments to run the script"""
    parser = argparse.ArgumentParser(description='Walk Generator')
    parser.add_argument('--config', '-c', required=True, help='YAML Configuration File for Walk Generator with path')
    return parser.parse_args()


def signal_handler(name):
    print( f'signal_handler {name}')
    global sighup_handler_var
    sighup_handler_var = True


async def app(eventloop, config_file):
    while True:
        walker = WalkPatternGenerator( eventloop=eventloop, config_file="personnel.yaml", personnel_id=1 )
        await walker.connect()
        global sighup_handler_var
        while not sighup_handler_var:
            await walker.run_once( tdelta=0.7, binding_key="telemetry" )
        del walker
        sighup_handler_var = False


def main():
    """Initialization"""
    args = parse_arguments()
    if not os.path.isfile( args.config ):
        logging.error( "configuration file not readable. Check path to configuration file" )
        sys.exit()

    event_loop = asyncio.get_event_loop()
    event_loop.add_signal_handler( signal.SIGHUP, functools.partial( signal_handler, name='SIGHUP' ) )
    event_loop.run_until_complete( app( event_loop,args.config ) )


if __name__ == "__main__":
    main()

