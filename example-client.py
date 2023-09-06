#!/usr/bin/env python3
import json
import requests
import os
import argparse
import re
import sys

from requests.auth import HTTPBasicAuth

_temp_file_name = '/tmp/example-client.run'

# This is a BETA URL and _Will Change_
_endpoint_url = 'https://5clcj0iz8c.execute-api.us-east-1.amazonaws.com/prod/logs'
_pagination_url = ''

_allowed_params = [
    'limit',
    'since',
    'until',
    'orgurl',
    'tenant',
    'service',
    'metrictype',
    'metricsubtype',
    'clientip',
    'correlationid',
    'user',
]

def _debug(*pargs, **kwargs):
    if args.v:
        print(*pargs, file=sys.stderr, **kwargs)

# Define command line arguments
_parser = argparse.ArgumentParser()
_parser.add_argument("--apikey", help="Specify the API key for auth. Alternatively, set it in the API_KEY environment variable")
_parser.add_argument("--apisecret", help="Specify the API secret for auth. Alternatively, set it in the API_SECRET environment variable")
_parser.add_argument("--apiurl", help="Specify a URL to override the default API URL of the Cirrus Logs API")
_parser.add_argument("--limit", type=int, default=1000, help="Limit number of entries to fetch from the API")
_parser.add_argument("--since", help="Time stamp to start search from. Default is 1 week in past. Format is ISO8601 but must include the trailing 'Z' e.g. \"YYYY-MM-DD HH:MM:SSZ\". Enclose the value in quotes to include spaces")
_parser.add_argument("--until", help="Time stamp to end search at. Default is now. Do not use if you want to stream logs. Format is ISO8601 but must include the trailing 'Z' e.g. \"YYYY-MM-DD HH:MM:SSZ\". Enclose the value in quotes to include spaces")
_parser.add_argument("--orgurl",help="specify the orgurl string to query against. Only needed if your API Key is authorized for more than one orgurl")
_parser.add_argument("--query",help="comma-separated list key=value pairs to narrow search. Possible keys are 'tenant','service','metrictype','metricsubtype','clientip','correlationid','user'")
_parser.add_argument("-c",action='store_true', help="Continuous. Run with this flag to stream logs, continuing where the last invocation left off" )
_parser.add_argument("-x",action='store_true', help="Exit after fetching one set of results, even if more results are available")
_parser.add_argument("-v",action='store_true', help="Print debugging info to STDERR")
args = _parser.parse_args()
_args_dict = vars(args)

if args.query:
    _search_params = dict(item.split("=") for item in args.query.split(","))
    for _param in _allowed_params:
        if _param in _search_params:
            _args_dict[_param] = _search_params[_param]
        
_api_key = args.apikey if args.apikey else os.getenv('API_KEY')
_api_secret = args.apisecret if args.apisecret else os.getenv('API_SECRET')
if _api_key is None or _api_secret is None:
    raise Exception("Missing API key or secret")
_credentials = HTTPBasicAuth(_api_key, _api_secret)

if args.orgurl:
    _orgUrl = args.orgurl

if args.apiurl:
    _endpoint_url = args.apiurl

if args.limit and args.limit > 1000:
    args.limit = 1000

if args.c:
    if os.path.exists(_temp_file_name):
        # If the temporary file exists, read the pagination URL from it
        with open(_temp_file_name, "r") as f:
            _pagination_url = f.read().strip()
            
_data = {}

while True:
    if re.search('; rel="next"$',_pagination_url):
        _endpoint_url = _pagination_url.replace('; rel="next"',"")
        _debug(f"Setting endpoint_url to {_endpoint_url}")

    # Since we're using a POST, the Lambda Server code won't include our query params in the pagination URL
    # So add our query params to the URL, regardless of whether this is the first or subsequent call
    _endpoint_url = f"{_endpoint_url}&" if re.search("after=",_endpoint_url) else f"{_endpoint_url}?"
    if _orgUrl != "":
        _endpoint_url = f"{_endpoint_url}orgUrl={_orgUrl}&"

    for _param in _allowed_params:
        if _param in _args_dict and not re.search(f"&{_param}",_endpoint_url) and _args_dict[_param]:
            _endpoint_url = f"{_endpoint_url}{_param}={_args_dict[_param]}&"

    _endpoint_url = _endpoint_url.rstrip('&?')
    _debug(f"Sending request to {_endpoint_url}")
    _resp = requests.post(_endpoint_url, auth=_credentials, json=_data)
    if _resp.status_code == 200:
        _results = _resp.json()
        print(json.dumps(_results, indent=4))
        if "link" in _resp.headers and not args.x:
            # If there are more pages, store the pagination URL in the temporary file
            _pagination_url = _resp.headers["link"]
            with open(_temp_file_name, "w") as f:
                f.write(_pagination_url)
            if len(_results) < args.limit:
                # We're at the end of the results
                _debug(f"Reached end of results. Limit: {args.limit}. Results: {len(_results)}")
                break
            else:
                _debug(f"Retrieved {len(_results)} results. More available - continuing")
        else:
            _debug("End of results reached - no pagination link present")
            break
    else:
        _resp.raise_for_status()

if not args.c and os.path.exists(_temp_file_name):
    # Not in continuous mode and we've reached the end of the results. Remove the pagination file
    _debug(f"Not running in continuous mode. Removing pagination file {_temp_file_name}")
    os.remove(_temp_file_name)
