# [who-hosts-hate](https://who-hosts-hate.com)

Who hosts hate on the internet?

## Requirements

- Python 3.7
- AWS account
  - Used for querying a site’s popularity ranking
- ipstack account
  - Used for querying a site’s host
  - ‘Basic’ tier or higher

## Setup

```sh
python3 -m venv .venv
source .venv/bin/activate # or `source .venv/bin/activate.fish`
pip install -r requirements.txt
```

## Build

Generate `index.html` via `build.py`.

```
usage: build.py [-h] ipstack_access_key aws_access_key_id aws_secret_access_key
```

## Legal

* `favicon.ico`: [Server by Arfan Khan Kamol from the Noun Project](https://thenounproject.com/term/server/2784476)
* All other files are licensed [CC0](https://creativecommons.org/publicdomain/zero/1.0/)
