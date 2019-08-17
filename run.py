import collections
import json
import pprint
import urllib.request
import argparse
import myawis
import typing
from xml.etree import ElementTree

parser = argparse.ArgumentParser()
parser.add_argument('ipstack_access_key')
parser.add_argument('aws_access_key_id')
parser.add_argument('aws_secret_access_key')
args = parser.parse_args()


def site_rank(site: str) -> typing.Optional[int]:
    obj = myawis.CallAwis(args.aws_access_key_id, args.aws_secret_access_key)
    urlinfo = obj.urlinfo(site)
    tree = ElementTree.fromstring(str(urlinfo))
    rank = tree.findall(
        './/aws:TrafficData/aws:Rank',
        {'aws': "http://awis.amazonaws.com/doc/2005-07-11"}
    )[0].text
    # TODO fetch `aws:ContributingSubdomain`
    return int(rank) if rank else None


sites = [
    '4chan.org',
    '8ch.net',
    'acpeds.org',
    'actforamerica.org',
    'adflegal.org',
    'americanfreedomalliance.org',
    'americanidentitymovement.com',
    'americannaziparty.com',
    'barenakedislam.com',
    'bloodandhonourworldwide.co.uk',
    'breitbart.com',
    'cfns.us',
    'conservative-headlines.org',
    'culturewars.com',
    'dailywire.com',
    'faithandheritage.com',
    'foxnews.com',
    'gab.com',
    'gellerreport.com',
    'godhatesfags.com',
    'infowars.com',
    'irvingbooks.com',
    'jihadwatch.org',
    'jtf.org',
    'kiwifarms.net',
    'leagueofthesouth.com',
    'natall.com',
    'nationalpolicy.institute',
    'nsm88.org',
    'officialproudboys.com',
    'patriotfront.us',
    'politicalislam.com',
    'prageru.com',
    'profam.org',
    'stormfront.org',
    'tightroperecords.com',
    'understandingthethreat.com',
    'unitedfamilies.org',
    'vachristian.org',
    'washsummit.com',
]

isps = collections.defaultdict(lambda: [])

for site in sites:
    response = urllib.request.urlopen(
        "http://api.ipstack.com/{}?access_key={}".format(
            site, args.ipstack_access_key),
    ).read()

    response_json = json.loads(response)

    isp = response_json['connection']['isp']

    rank = site_rank(site)

    isps[isp].append([site, rank])

pp = pprint.PrettyPrinter(indent=4)
pp.pprint(dict(isps))
