import shutil
from pathlib import Path

import pytest
import requests
from bs4 import BeautifulSoup

from pixelripper.pixelripper import PixelRipper, PixelRipperSelenium
from scrapetools import LinkScraper

root = Path(__file__).parent

# Find new url, audio downloads to download correctly without
# appending "?raw=true" to the end.
url = "https://github.com/matt-manes/voxscribeTestAudio"


def test__pixelripper__is_this_thing_on():
    ripper = PixelRipper()


def test__pixelripper__get():
    ripper = PixelRipper()
    response = ripper.get(url)
    assert type(response) == requests.Response
    assert response.status_code == 200
    ripper = PixelRipperSelenium()
    response = ripper.get(url)
    assert response.url == url
    assert len(response.text) > 0


@pytest.mark.parametrize("ripper_class", (PixelRipper, PixelRipperSelenium))
def test__pixelripper__rip(ripper_class: PixelRipper | PixelRipperSelenium):
    ripper = ripper_class()
    ripper.rip(url)
    assert type(ripper.scraper) == LinkScraper
    for url_list in [ripper.image_urls, ripper.video_urls, ripper.audio_urls]:
        assert type(url_list) == list
    assert len(ripper.image_urls) > 0
    assert len(ripper.video_urls) == 0
    assert len(ripper.audio_urls) == 2


def test__pixelripper__filter_by_extensions():
    ...


def test__pixelripper__download_files():
    ripper = PixelRipper()
    ripper.rip(url)
    failures = ripper.download_files(
        ripper.image_urls, (root / "downloads"), missing_ext_sub=".jpg"
    )
    assert len(failures) == 0
    assert len(list((root / "downloads").iterdir())) > 0
    shutil.rmtree(root / "downloads")


def test__pixelripper__download_all():
    ripper = PixelRipper()
    ripper.rip(url)
    failures = ripper.download_all(root / "downloads")
    for link_type in failures:
        assert len(failures[link_type]) == 0
    assert len(list((root / "downloads" / "images").iterdir())) > 0
    assert len(list((root / "downloads" / "audio").iterdir())) == 2
    assert not (root / "downloads" / "videos").exists()


def test__pixelripper__get_args():
    ...


def test__pixelripper__main():
    ...
