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

from xml.etree import ElementTree

import jinja2
import myawis


HATE_SITES_CSV_DEFAULT_PATH = 'hate-sites.csv'

OUTPUT_DIR = 'build'


ASN_NAME_MAP = {
    15169: "Google",
    26347: "DreamHost",
    36647: "Oath (Yahoo)",
    54113: "Fastly",
}


def site_rank(site: str) -> typing.Optional[int]:
    while True:
        obj = myawis.CallAwis(args.aws_access_key_id, args.aws_secret_access_key)
        try:
            urlinfo = obj.urlinfo(site)
            break
        except requests.exceptions.ConnectionError:
            log_error(site, "AWIS connection error, trying again")
    try:
        tree = ElementTree.fromstring(str(urlinfo))
    except ElementTree.ParseError:
        log_error(site, "Could not retrieve rank")
        return None
    results = tree.findall(
        './/aws:TrafficData/aws:Rank',
        {'aws': "http://awis.amazonaws.com/doc/2005-07-11"}
    )
    if not results:
        log_error(site, 'Could not find rank')
        return None
    rank = tree.findall(
        './/aws:TrafficData/aws:Rank',
        {'aws': "http://awis.amazonaws.com/doc/2005-07-11"}
    )[0].text
    log_info(site, f"Found site rank: {rank}")
    # TODO fetch `aws:ContributingSubdomain`
    return int(rank) if rank else None


def log_info(site: str, s: str):
    logging.info(f"{site} - {s}")


def log_error(site: str, s: str):
    logging.error(f"{site} - {s}")


class Asn(typing.NamedTuple):
    name: str
    number: int


def site_isp(site: str) -> typing.Optional[Asn]:
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


def sites() -> [[str, str]]:
    with open(args.hate_sites_csv_path) as f:
        reader = csv.reader(f)
        next(reader) # Skip the heading row
        return list(reader)


def build_isps_data():
    isps = collections.defaultdict(lambda: [])

    for site, hate_reason, _ in sites():
        isp = site_isp(site)
        if isp is None:
            continue

        rank = site_rank(site)

        if hate_reason != 'splc':
            hate_reason = None

        isps[isp].append([mask_site(site), rank_to_rank_group(rank), rank_to_color(rank), hate_reason])

    return sorted(isps.items(), key=lambda x: len(x[1]), reverse=True)


def mask_site(site: str) -> str:
    domain = site.split(".")[-1]
    num_asterisks = len(site) - len(domain) - 2
    asterisks = "*" * num_asterisks
    return f"{site[0]}{asterisks}.{domain}"


def rank_to_rank_group(rank: typing.Optional[int]) -> str:
    if rank and rank < 10_000:
        return '<10K'
    elif rank and rank < 100_000:
        return '10K-100K'
    elif rank and rank < 1_000_000:
        return '100K-1M'
    elif rank and rank < 10_000_000:
        return '1M-10M'
    else:
        return '≥10M'


def rank_to_color(rank: typing.Optional[int]) -> str:
    if rank and rank < 10_000:
        return '#fff600'
    elif rank and rank < 100_000:
        return '#d7d45d'
    elif rank and rank < 1_000_000:
        return '#c9c77f'
    elif rank and rank < 10_000_000:
        return '#bcbc9d'
    else:
        return '#b3b3b3'


def todays_date() -> str:
    return datetime.datetime.now().strftime("%B %d, %Y")


def render():
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader('templates'),
    )

    template = env.get_template('index.html.j2')

    if not os.path.exists(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)

    with open(os.path.join(OUTPUT_DIR, 'index.html'), 'w') as f:
        f.write(template.render(
            isps_data=build_isps_data(),
        ))

    template = env.get_template('faqs.html.j2')

    with open(os.path.join(OUTPUT_DIR, 'faqs.html'), 'w') as f:
        f.write(template.render(
            todays_date=todays_date(),
        ))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('aws_access_key_id')
    parser.add_argument('aws_secret_access_key')
    parser.add_argument('--hate-sites-csv-path', default=HATE_SITES_CSV_DEFAULT_PATH)
    parser.add_argument('--log', action='store_true')
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    if not args.log:
        logging.disable(logging.CRITICAL)

    render()
