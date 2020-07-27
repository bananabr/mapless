#!/usr/bin/env python

"""
This is a PoC port mapper that uses the mapless API
"""

import os
import json
import asyncio
from multiprocessing import Pool
from optparse import OptionParser
import logging
import socket

import aiohttp

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-U", "--url", dest="base_url",
                      help="the mapless api base url (eg.: https://0000000000.execute-api.us-east-1.amazonaws.com)")
    parser.add_option("-K", "--api-key", dest="api_key",
                      help="the mapless api key (eg.: 5ViTxWEDxR3Rk9T5tTquV5VktPKlBP8Z9QjHcqe1)")
    parser.add_option("-H", "--host", dest="host",
                      help="hostname/IP")
    parser.add_option("-p", "--ports", dest="ports",
                      help="ports (eg: 22; 1-1024; 80,443)")
    parser.add_option("-f", "--file", dest="targets_file",
                      help="csv file with targets (format: ip, port)")
    parser.add_option("-r", "--rate-limit", type=int, dest="rate_limit", default=32,
                      help="thread count (default: 32)")
    parser.add_option("-t", "--timeout", type=int, dest="timeout", default=3,
                      help="port connection timeout (default: 3)")
    parser.add_option("-v", "--verbose",
                      action="store_true", dest="verbose", default=False,
                      help="print INFO level messages to stdout")
    parser.add_option("-d", "--debug",
                      action="store_true", dest="debug", default=False,
                      help="print DEBUG level messages to stdout")

    (options, args) = parser.parse_args()

    if options.verbose:
        logging.basicConfig(level=logging.INFO)
    elif options.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)
    
    BASE_URL = os.environ.get('MAPLESS_BASE_URL', options.base_url)
    ENDPOINT = f'/dev/portscan'
    URL = f'{BASE_URL}{ENDPOINT}'
    APIKEY = os.environ.get('MAPLESS_API_KEY', options.api_key)
    HEADERS = {'X-API-KEY': APIKEY, 'Content-Type': 'application/json'}
    CONNECTOR = aiohttp.TCPConnector(limit_per_host=options.rate_limit)
    SESSION = aiohttp.ClientSession(headers=HEADERS, connector=CONNECTOR)
    LOOP = asyncio.get_event_loop()

    async def test_port(host, port, timeout=5):
        params = {'host': host, 'port': port, 'timeout': timeout}

        async with SESSION.get(URL, params=params) as resp:
            data = await resp.json()
            logging.info(f"{host}:{port}")
            logging.debug(data)
            return data

    async def close_session():
        await SESSION.close()

    ports = []
    if ',' in options.ports:
        ports = map(lambda p: int(p), options.ports.split(','))
    elif '-' in options.ports:
        ports = range(int(options.ports.split('-')[0]),
                      int(options.ports.split('-')[1]))
    else:
        ports = [int(options.ports)]

    scan_args = []
    for port in ports:
        if options.targets_file:
            import csv
            with open(options.targets_file, 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                scan_args = list(map(lambda row: {
                    'host': row['ip'],
                    'port': port,
                    'timeout': options.timeout
                }, reader))
        else:
            scan_args.append({
                'host': options.host,
                'port': port,
                'timeout': options.timeout
            })

    result = LOOP.run_until_complete(
        asyncio.gather(
            *(test_port(**args) for args in scan_args)
        )
    )
    LOOP.run_until_complete(close_session())
    print(result)
