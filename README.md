# Requirements

- Python 3.7

# Setup

```sh
python3 -m venv .venv
source .venv/bin/activate # or `source .venv/bin/activate.fish`
pip install -r requirements.txt
```

# Run

```
$ python run.py <IPSTACK ACCESS KEY>
{   'Akamai Technologies, Inc.': ['foxnews.com'],
    'Cloudflare, Inc.': [   'dailywire.com',
                            'infowars.com',
                            '4chan.org',
                            'godhatesfags.com',
                            'kiwifarms.net',
                            'stormfront.org',
                            'gab.com'],
    'Google LLC': ['breitbart.com', 'officialproudboys.com', 'prageru.com'],
    'N.T. Technology, Inc.': ['8ch.net']}
```
