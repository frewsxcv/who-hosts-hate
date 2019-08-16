import collections
import json
import pprint
import urllib.request
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('ipstack_access_key')
args = parser.parse_args()

sites = [
    '4chan.org',
    '8ch.net',
    'americannaziparty.com',
    'americanidentitymovement.com',
    'americanfreedomalliance.org',
    'acpeds.org',
    'adflegal.org',
    'actforamerica.org',
    'barenakedislam.com',
    'bloodandhonourworldwide.co.uk',
    'breitbart.com',
    'conservative-headlines.org',
    'culturewars.com',
    'dailywire.com',
    'foxnews.com',
    'gab.com',
    'gellerreport.com',
    'godhatesfags.com',
    'infowars.com',
    'jihadwatch.org',
    'kiwifarms.net',
    'leagueofthesouth.com',
    'natall.com',
    'nationalpolicy.institute',
    'nsm88.org',
    'officialproudboys.com',
    'patriotfront.us',
    'prageru.com',
    'stormfront.org',
    'understandingthethreat.com',
    'washsummit.com',
]

isps = collections.defaultdict(lambda: [])

for site in sites:
    response = urllib.request.urlopen(
        "http://api.ipstack.com/{}?access_key={}".format(site, args.ipstack_access_key),
    ).read()

    response_json = json.loads(response)

    isp = response_json['connection']['isp']

    isps[isp].append(site)

pp = pprint.PrettyPrinter(indent=4)
pp.pprint(dict(isps))
