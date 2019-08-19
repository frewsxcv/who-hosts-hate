#!/usr/bin/env python

import argparse
import collections
import datetime
import json
import logging
import pprint
import typing
import urllib.request

from xml.etree import ElementTree

import jinja2
import myawis


def site_rank(site: str) -> typing.Optional[int]:
    logging.info('Fetching site rank for {}'.format(site))
    obj = myawis.CallAwis(args.aws_access_key_id, args.aws_secret_access_key)
    urlinfo = obj.urlinfo(site)
    tree = ElementTree.fromstring(str(urlinfo))
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

    return response_json['connection']['isp']


def sites() -> [str]:
    with open('domains.txt') as f:
        return f.read().strip().splitlines()


def build_isps_data():
    isps = collections.defaultdict(lambda: [])

    for site in sites():
        isp = site_isp(site)
        rank = site_rank(site)
        isps[isp].append([site, rank, rank_to_color(rank)])

    return sorted(isps.items(), key=lambda x: len(x[1]), reverse=True)


def rank_to_color(rank: typing.Optional[int]) -> str:
    if rank and rank < 10000:
        return 'yellow'
    elif rank and rank < 100000:
        return 'white'
    else:
        return '#999999'


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
