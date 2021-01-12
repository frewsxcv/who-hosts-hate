#!/usr/bin/env python

import argparse
import collections
import csv
import datetime
import json
import logging
import os
import pprint
import typing
import hashlib
import socket
import requests
import geoip2.database
import urllib.request
import whois

import jinja2


HATE_SITES_CSV_DEFAULT_PATH = 'hate-sites.csv'

OUTPUT_DIR = 'build'


ASN_NAME_MAP = {
    15169: "Google",
    26347: "DreamHost",
    36647: "Oath (Yahoo)",
    54113: "Fastly",
}


def log_info(site: str, s: str):
    logging.info(f"{site} - {s}")


def log_error(site: str, s: str):
    logging.error(f"{site} - {s}")


class Asn(typing.NamedTuple):
    name: str
    number: int


def site_isp(site: str) -> typing.Optional[Asn]:
    # log_info(site, f"Domain registrar: {whois.query(site).registrar}")
    try:
        ip = socket.gethostbyname(site)
    except socket.gaierror:
        log_error(site, "Could not DNS resolve")
        return
    with geoip2.database.Reader('GeoLite2-ASN.mmdb') as reader:
        try:
            response = reader.asn(ip)
        except geoip2.errors.AddressNotFoundError:
            log_error(site, "Could not find address in GeoLite2 DB")
            return
    isp = (
        ASN_NAME_MAP.get(response.autonomous_system_number) or
        asn_name(response.autonomous_system_number) or
        response.autonomous_system_organization
    )
    log_info(site, f"Found ISP: {isp}")
    return Asn(name=isp, number=response.autonomous_system_number)


def asn_name(asn_id: int) -> typing.Optional[str]:
    # https://www.peeringdb.com/apidocs/#operation/retrieve%20net
    url = f"https://peeringdb.com/api/net?asn={asn_id}"
    response_json = requests.get(url).json()
    if not response_json['data']:
        return
    return response_json['data'][0]['name']


def sites(limit=None) -> [[str, str, str]]:
    with open(args.hate_sites_csv_path) as f:
        reader = csv.reader(f)
        next(reader) # Skip the heading row
        if limit:
            return list(reader)[:limit]
        else:
            return list(reader)


def build_isps_data(limit=None):
    isps = collections.defaultdict(lambda: [])

    for site, classification, _, page_string in sites(limit=limit):
        isp = site_isp(site)
        if isp is None:
            continue

        hate_site_response = HateSiteLoader(domain=site).load()
        is_site_up = isinstance(
            HateSiteResponseAnalyzer(response=hate_site_response, page_string=page_string).analyze(),
            HateSiteResponseSiteUp
        )

        if classification != 'splc' and classification != 'islamophobia':
            classification = None

        isps[isp].append([mask_site(site), is_site_up, classification])

    return sorted(isps.items(), key=lambda x: len(x[1]), reverse=True)


def mask_site(site: str) -> str:
    domain = site.split(".")[-1]
    num_asterisks = len(site) - len(domain) - 2
    asterisks = "•" * num_asterisks
    return f"{site[0]}{asterisks}.{domain}"


def todays_date() -> str:
    return datetime.datetime.now().strftime("%B %d, %Y")


CHROME_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'
REQUEST_HEADERS = {'User-Agent': CHROME_USER_AGENT}


class HateSiteErrorResponse(typing.NamedTuple):
    reason: str
    status_code: typing.Optional[int]


class HateSiteResponse(typing.NamedTuple):
    body: bytes
    status_code: int


class HateSiteLoader(typing.NamedTuple):
    domain: str

    def load(self) -> typing.Union[HateSiteResponse, HateSiteErrorResponse]:
        url = 'http://' + self.domain
        request = urllib.request.Request(url, headers=REQUEST_HEADERS)
        try:
            response = urllib.request.urlopen(request)
        except urllib.error.HTTPError as error:
            return HateSiteErrorResponse(reason=str(error.reason), status_code=error.code)
        except urllib.error.URLError as error:
            return HateSiteErrorResponse(reason=str(error.reason), status_code=None)
        except TimeoutError as error:
            return HateSiteErrorResponse(reason="Timeout", status_code=None)
        return HateSiteResponse(body=response.read(), status_code=response.status)


class HateSiteResponseSiteUp:
    pass


class HateSiteResponsePageStringNotFound:
    pass


class HateSiteResponseSiteDown(typing.NamedTuple):
    status_code: typing.Optional[int]
    reason: str


class HateSiteResponseAnalyzer(typing.NamedTuple):
    response: typing.Union[HateSiteResponse, HateSiteErrorResponse]
    page_string: str

    def analyze(self) -> typing.Union[HateSiteResponseSiteUp, HateSiteResponsePageStringNotFound, HateSiteResponseSiteDown]:
        if isinstance(self.response, HateSiteResponse):
            if self.page_string.encode() in self.response.body:
                return HateSiteResponseSiteUp()
            else:
                return HateSiteResponsePageStringNotFound()
        elif self.response.status_code:
            return HateSiteResponseSiteDown(status_code=self.response.status_code, reason=self.response.reason)
        else:
            return HateSiteResponseSiteDown(status_code=None, reason=self.response.reason)


def render(limit=None):
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader('templates'),
    )

    template = env.get_template('index.html.j2')

    if not os.path.exists(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)

    with open(os.path.join(OUTPUT_DIR, 'index.html'), 'w') as f:
        f.write(template.render(
            isps_data=build_isps_data(limit=limit),
        ))

    template = env.get_template('faqs.html.j2')

    with open(os.path.join(OUTPUT_DIR, 'faqs.html'), 'w') as f:
        f.write(template.render(
            todays_date=todays_date(),
        ))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--hate-sites-csv-path', default=HATE_SITES_CSV_DEFAULT_PATH)
    parser.add_argument('--log', action='store_true')
    parser.add_argument('--limit', type=int, help='Limit the number of sites to process')
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    if not args.log:
        logging.disable(logging.CRITICAL)

    render(limit=args.limit)
