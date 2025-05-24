# issuu-dl

Download JPEGs from https://issuu.com/ and combine them in a PDF.

Based off of https://github.com/Mustkeem324/Issuu-PDF-Downloader/blob/main/main.py.

## Installation

After cloning this repository, do the following to install requirements in a virtual environment.

```bash
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
```

## Usage

```
usage: issuu-dl.py [-h] -u URL [-v]

options:
  -h, --help     show this help message and exit
  -u, --url URL  Issuu URL
  -v, --verbose  Increase logging verbosity to logging.DEBUG
```
