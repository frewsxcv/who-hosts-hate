#!/usr/bin/env python

import argparse
import collections
import csv
import datetime
import json
import logging
import pprint
import typing
import requests
import urllib.request

from xml.etree import ElementTree

import jinja2
import myawis


ISP_NAME_MAP = {
    "New Dream Network, LLC": "New Dream Network, LLC (DreamHost)",
    "Softlayer Technologies Inc.": "Softlayer Technologies Inc. (IBM)",
}


def site_rank(site: str) -> typing.Optional[int]:
    logging.info('Fetching site rank for {}'.format(site))
    while True:
        obj = myawis.CallAwis(args.aws_access_key_id, args.aws_secret_access_key)
        try:
            urlinfo = obj.urlinfo(site)
            break
        except requests.exceptions.ConnectionError:
            logging.error("AWIS connection error, trying again".format(site))
            pass
    try:
        tree = ElementTree.fromstring(str(urlinfo))
    except ElementTree.ParseError:
        logging.error("Could not retrieve rank for {}".format(site))
        return None
    rank = tree.findall(
        './/aws:TrafficData/aws:Rank',
        {'aws': "http://awis.amazonaws.com/doc/2005-07-11"}
    )[0].text
    # TODO fetch `aws:ContributingSubdomain`
    return int(rank) if rank else None


def site_isp(site: str) -> str:
    logging.info('Fetching site ISP for {}'.format(site))
    response = urllib.request.urlopen(
        "http://api.ipstack.com/{}?access_key={}".format(
            site, args.ipstack_access_key),
    ).read()

    response_json = json.loads(response)

    isp_name = response_json['connection']['isp']

    return ISP_NAME_MAP.get(isp_name, isp_name)


def sites() -> [[str, str]]:
    with open('domains.csv') as f:
        return list(csv.reader(f))


def build_isps_data():
    isps = collections.defaultdict(lambda: [])

    for site, hate_reason in sites():
        isp = site_isp(site)
        rank = site_rank(site)

        if hate_reason != 'splc':
            hate_reason = None

        isps[isp].append([site, rank, rank_to_color(rank), hate_reason])

    return sorted(isps.items(), key=lambda x: len(x[1]), reverse=True)


def rank_to_color(rank: typing.Optional[int]) -> str:
    if rank and rank < 10000:
        return '#fff600'
    elif rank and rank < 100000:
        return '#d7d45d'
    elif rank and rank < 1000000:
        return '#c9c77f'
    elif rank and rank < 10000000:
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

    with open('index.html', 'w') as f:
        f.write(template.render(
            isps_data=build_isps_data(),
        ))

    template = env.get_template('faqs.html.j2')

    with open('faqs.html', 'w') as f:
        f.write(template.render(
            todays_date=todays_date(),
        ))

parser = argparse.ArgumentParser()
parser.add_argument('ipstack_access_key')
parser.add_argument('aws_access_key_id')
parser.add_argument('aws_secret_access_key')
args = parser.parse_args()

logging.basicConfig(level=logging.INFO)

render()
