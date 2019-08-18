# who-hosts-hate

Which companies host hate sites?

## Requirements

- Python 3.7

## Setup

```sh
python3 -m venv .venv
source .venv/bin/activate # or `source .venv/bin/activate.fish`
pip install -r requirements.txt
```

## Run

Generate `index.html` via `build.py`.

```
usage: build.py [-h] ipstack_access_key aws_access_key_id aws_secret_access_key
```
