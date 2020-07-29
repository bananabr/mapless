#!/usr/bin/env python

"""
This is a PoC port mapper that uses the mapless API
"""

import json
import os
import asyncio
from multiprocessing import Pool
from optparse import OptionParser
import logging
import socket

import aiohttp

async def main():
    parser = OptionParser()
    parser.add_option("-U", "--url", dest="base_url",
                      help="the mapless api base url (eg.: https://0000000000.execute-api.us-east-1.amazonaws.com)")
    parser.add_option("-K", "--api-key", dest="api_key",
                      help="the mapless api key (eg.: 5ViTxWEDxR3Rk9T5tTquV5VktPKlBP8Z9QjHcqe1)")
    parser.add_option("-H", "--host", dest="host",
                      help="hostname/IP")
    parser.add_option("-p", "--port", type=int, dest="port", default=80,
                      help="port (default: 80)")
    parser.add_option("-u", "--user", dest="username", default='root',
                      help="username")
    parser.add_option("-P", "--password", dest="password_file",
                      help="file with passwords")
    parser.add_option("", "--proto", dest="proto", default="http",
                      help="supported protocol [http, ssh, ami] (default: http)")
    parser.add_option("-f", "--file", dest="targets_file",
                      help="csv file with targets (format: ip, port)")
    parser.add_option("-r", "--rate-limit", type=int, dest="rate_limit", default=32,
                      help="thread count (default: 32)")
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
    ENDPOINT = f'/dev/login/{options.proto}'
    URL = f'{BASE_URL}{ENDPOINT}'
    APIKEY = os.environ.get('MAPLESS_API_KEY', options.api_key)
    HEADERS = {'X-API-KEY': APIKEY, 'Content-Type': 'application/json'}
    logging.debug(f'HEADERS: {HEADERS}')
    CONNECTOR = aiohttp.TCPConnector(limit_per_host=options.rate_limit, ttl_dns_cache=100)


    async def test_auth(session, host, port, username, password):
        params = {'host': host, 'port': port,
                  'username': username, 'password': password}
        async with session.get(URL, params=params) as resp:
            data = await resp.json()
            logging.info(f"{username}:{password}@{host}:{port}")
            logging.debug(data)
            status = data.get("statusCode", 500)
            if status == 200:
                logging.critical(data)

    with open(options.password_file, 'r') as password_file:
        async with aiohttp.ClientSession(headers=HEADERS, connector=CONNECTOR) as session:
            scan_args = []    
            for password in password_file.readlines():
                if options.targets_file:
                    import csv
                    with open(options.targets_file, 'r') as csvfile:
                        reader = csv.DictReader(csvfile)
                        scan_args = list(map(lambda row: {
                            'host': row['ip'],
                            'port': row['port'],
                            'username': options.username,
                            'password': password.strip(),
                            'session': session
                        }, reader))
                else:
                    scan_args.append({
                        'host': options.host,
                        'port': options.port,
                        'username': options.username,
                        'password': password.strip(),
                        'session': session
                    })

            await asyncio.gather(
                *(test_auth(**args) for args in scan_args)
            )

if __name__ == "__main__":
    asyncio.run(main())