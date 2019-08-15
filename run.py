import collections
import json
import pprint
import urllib.request
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('ipstack_access_key')
args = parser.parse_args()

sites = [
    'dailywire.com',
    '8ch.net',
    'foxnews.com',
    'infowars.com',
    'breitbart.com',
    '4chan.org',
    'officialproudboys.com',
    'godhatesfags.com',
    'kiwifarms.net',
    'prageru.com',
    'stormfront.org',
    'gab.com',
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
