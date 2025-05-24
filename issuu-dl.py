"""
issuu_dl.py

A command-line utility to download an Issuu document's pages as images
and convert them into a single PDF file. The tool uses multithreading to 
download images concurrently and saves the final PDF using the Pillow library.

This is an improvement on https://github.com/Mustkeem324/Issuu-PDF-Downloader/blob/main/main.py
- Uses a session instead of individual requests to reduce dns resolutions
- General code cleanliness
- Removal of extraneous, unecessary functionality
- Replacing interactive user input with argparse for easier scripting
- Remove concurrency but add progress percentage

Docstrings courtesy of ChatGPT. No code was generated with an LLM (unless the original was).

Usage:
    python issuu_dl.py -u <issuu_document_url> [-v]

Arguments:
    -u, --url     Required. Full Issuu document URL to download.
    -v, --verbose Optional. Enables debug-level logging.
"""

import os
import sys
import requests
import argparse
import logging
import json
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
from io import BytesIO
import urllib.parse
    
ISSUU_URL = 'https://issuu.com/'
HEADERS = {
    'User-Agent':'issuu-dl'
}


def download_image(session: requests.Session, url: str) -> BytesIO | None:
    """
    Download a single image from the given URL using the provided session.

    Args:
        session (requests.Session): The requests session to use for the download.
        url (str): The image URL.

    Returns:
        BytesIO: A BytesIO object containing image data, or None if download fails.
    """
    resp = session.get(url, headers=HEADERS)
    logging.debug("Downloading image: %s", url)
    if resp.status_code == 200:
        return BytesIO(resp.content)
    else:
        logging.error("Image URL %s received bad status code %s", url, resp.status_code)


def download_images(session: requests.Session, image_urls: list[str]) -> list[BytesIO]:
    """
    Kick off multiple images concurrently using a thread pool.

    Args:
        session (requests.Session): The requests session to use for downloads.
        image_urls (list[str]): List of image URLs to download.

    Returns:
        list[BytesIO]: A list of BytesIO objects containing image data.
    """
    logging.info("Beginning concurrent downloads")
    images = []
    for idx, url in enumerate(image_urls):
        images.append(download_image(session, url))
        sys.stdout.write(f"Downloaded {100*(idx/len(image_urls)):.0f}%\r")
        sys.stdout.flush()
    return images


def convert_images_to_pdf(images: list[BytesIO], document_name: str) -> None:
    """
    Convert a list of image data into a single PDF file using Pillow.

    Args:
        images (list[BytesIO]): A list of BytesIO image objects.
        document_name (str): The base name of the output PDF file.
    """
    logging.info("Converting images to PDF and saving to %s", f"{document_name}.pdf")
    pdf_images = []
    for idx, image in enumerate(images):
        img = Image.open(image)
        pdf_images.append(img)

    pdf_images[0].save(f"{document_name}.pdf", save_all=True, append_images=pdf_images[1:]) 


def fetch_metadata(session: requests.Session, urlobj: urllib.parse.ParseResult) -> dict:
    """
    Fetches document metadata JSON from Issuu's reader API based on the given URL object.

    The function extracts the account and document names from the parsed URL path,
    constructs the URL for the API endpoint, and parses the gathered JSON metadata.

    Args:
        session (requests.Session): The HTTP session used to send the request.
        urlobj (urllib.parse.ParseResult): A parsed URL object pointing to the Issuu document.

    Returns:
        tuple[str, dict]: A tuple containing the document name and its associated metadata.
    """
    parts = urlobj.path.strip('/').split('/')

    if len(parts) < 3:
        logging.error("Unrecognized URL path %s", urlobj.path)
        sys.exit(1)

    account_name    = parts[0]
    document_name   = parts[-1]
    url = f"https://reader3.isu.pub/{account_name}/{document_name}/reader3_4.json"

    logging.debug("Sending metadata request")
    resp = session.get(url, headers=HEADERS)

    if resp.status_code != 200:
        logging.error("Failed with response code %s", resp.status_code)
        sys.exit(1)

    return document_name, json.loads(resp.text)


def main(urlobj: urllib.parse.ParseResult) -> None:
    """
    Main execution flow for downloading and converting an Issuu document.

    Args:
        urlobj (urllib.parse.ParseResult): A parsed URL object from urllib.parse.
    """
    session = requests.Session()

    document_name, metadata = fetch_metadata(session, urlobj)
    image_urls = [f"https://{page['imageUri']}" for page in metadata['document']['pages']]
    logging.info("Downloading %s pages", len(image_urls))

    images = download_images(session, image_urls)

    convert_images_to_pdf(images, document_name)


def parse_args() -> object:
    """
    Parse command-line arguments.

    Returns:
        object: Parsed arguments with 'url' and 'verbose' attributes.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-u','--url',
        help='Issuu URL',
        required = True,
        type=str
    )
    parser.add_argument(
        '-v','--verbose',
        help='Increase logging verbosity to logging.DEBUG',
        action='store_true'
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level)

    if args.url is None or args.url[:len(ISSUU_URL)] != ISSUU_URL:
        logging.error(f"Invalid URL")
        sys.exit(1)

    urlobj = urllib.parse.urlparse(args.url)

    main(urlobj)
