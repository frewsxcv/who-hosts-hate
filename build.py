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
import socket
import requests
import geoip2.database
import urllib.request

from xml.etree import ElementTree

import jinja2
import myawis


HATE_SITES_CSV_DEFAULT_PATH = 'hate-sites.csv'

OUTPUT_DIR = 'build'

ISP_NAME_MAP = {
    "New Dream Network, LLC": "New Dream Network, LLC (DreamHost)",
    "Softlayer Technologies Inc.": "Softlayer Technologies Inc. (IBM)",
}


def site_rank(site: str) -> typing.Optional[int]:
    while True:
        obj = myawis.CallAwis(args.aws_access_key_id, args.aws_secret_access_key)
        try:
            urlinfo = obj.urlinfo(site)
            break
        except requests.exceptions.ConnectionError:
            logging.error("AWIS connection error, trying again")
    try:
        tree = ElementTree.fromstring(str(urlinfo))
    except ElementTree.ParseError:
        logging.error("Could not retrieve rank for {}".format(site))
        return None
    results = tree.findall(
        './/aws:TrafficData/aws:Rank',
        {'aws': "http://awis.amazonaws.com/doc/2005-07-11"}
    )
    if not results:
        logging.error('Could not find rank')
        return None
    rank = tree.findall(
        './/aws:TrafficData/aws:Rank',
        {'aws': "http://awis.amazonaws.com/doc/2005-07-11"}
    )[0].text
    logging.info('{} – Found site rank: {}'.format(site, rank))
    # TODO fetch `aws:ContributingSubdomain`
    return int(rank) if rank else None


def site_isp(site: str) -> str:
    try:
        ip = socket.gethostbyname(site)
    except socket.gaierror:
        logging.error("Could not DNS resolve {}".format(site))
        return '<unknown>'
    with geoip2.database.Reader('GeoLite2-ASN.mmdb') as reader:
        try:
            response = reader.asn(ip)
        except geoip2.errors.AddressNotFoundError:
            logging.error('{} – Could not find address in GeoLite2 DB'.format(site))
            return '<unknown>'
    isp = ISP_NAME_MAP.get(
        response.autonomous_system_organization,
        response.autonomous_system_organization,
    )
    logging.info('{} – Found ISP: {}'.format(site, isp))
    return isp


def sites() -> [[str, str]]:
    with open(args.hate_sites_csv_path) as f:
        reader = csv.reader(f)
        next(reader) # Skip the heading row
        return list(reader)


def build_isps_data():
    isps = collections.defaultdict(lambda: [])

    for site, hate_reason in sites():
        isp = site_isp(site)
        rank = site_rank(site)

        if hate_reason != 'splc':
            hate_reason = None

        isps[isp].append([mask_site(site), rank, rank_to_color(rank), hate_reason])

    return sorted(isps.items(), key=lambda x: len(x[1]), reverse=True)


def mask_site(site: str) -> str:
    domain = site.split(".")[-1]
    num_asterisks = len(site) - len(domain) - 2
    return "{}{}.{}".format(site[0], "*" * num_asterisks, domain)


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
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    render()
