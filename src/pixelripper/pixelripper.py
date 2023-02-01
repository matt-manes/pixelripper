import argparse
import shutil
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from printbuddies import ProgBar
from seleniumuser import User
from whosyouragent import get_agent

from scrapetools import LinkScraper

root = Path(__file__).parent


class PixelRipper:
    """Scrape and download media links."""

    def __init__(self):
        self.scraper: LinkScraper
        self.source_url: str
        self.savedir: str | Path
        self.video_exts: list[str] = (
            (root / "video_extensions.txt").read_text().splitlines()
        )
        self.audio_exts: list[str] = (
            (root / "audio_extensions.txt").read_text().splitlines()
        )
        self.image_urls: list[str]
        self.video_urls: list[str]
        self.audio_urls: list[str]

    def get(self, url: str, extra_headers: dict[str, str] = {}) -> requests.Response:
        """Construct and make request for a give url.
        Returns a requests.Response object.

        :param extra_headers: By default, only a
        random user-agent string is used in
        the request header, but additional
        key-value pairs can be added via this param."""
        headers = {"User-Agent": get_agent()}
        headers |= extra_headers
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise RuntimeError(
                f"getting {url} failed with response code {response.status_code}."
            )
        return response

    def rip(self, url: str, extra_headers: dict[str, str] = {}):
        """Scrape page and store urls in a LinkScraper object.

        :param url: The url to scrape for media content.

        :param extra_headers: Any additional HTTP headers to submit
        with the request."""
        response = self.get(url, extra_headers=extra_headers)
        self.scraper = LinkScraper(response.text, response.url)
        self.scraper.scrape_page()
        self.image_urls = [
            url
            for url in self.scraper.get_links("img")
            if not url.strip().strip("/").endswith(".com")
            and "apple-touch-icon" not in url.lower()
            and "favicon" not in url.lower()
        ]
        self.video_urls = self.filter_by_extensions(
            self.video_exts, self.image_urls
        ) + [
            url
            for url in self.scraper.get_links("all", excluded_links=self.image_urls)
            if "video" in urlparse(url).path
        ]
        self.audio_urls = self.filter_by_extensions(
            self.audio_exts, self.image_urls + self.video_urls
        ) + [
            url
            for url in self.scraper.get_links("all", excluded_links=self.image_urls)
            if "audio" in urlparse(url).path
        ]

    def filter_by_extensions(self, extensions: list[str], ignores: list[str] = []):
        """Return file urls from self.scraper
        according to a list of extensions.

        :param extensions: List of file extensions.
        Return urls that have an extension matching one in this list.

        :param ignores: List of urls. Filter out any urls
        in this list regardless of whether they have
        an extension matching one in the extensions param."""
        return [
            url.lower()
            for url in self.scraper.get_links("all", excluded_links=ignores)
            if any(ext == Path(url).suffix.lower() for ext in extensions)
        ]

    def download_files(
        self,
        urls: list[str],
        dst: Path | str,
        extra_headers: dict = None,
        missing_ext_sub: str = "",
    ) -> list[(str, int | None)]:
        """Download a list of files.

        :param urls: A list of urls to download

        :param dst: The destination path to save the files to.

        :param extra_headers: Any additional headers
        to be added to the request.

        :param missing_ext_sub: A file extension to use for
        the saved file if the url doesn't have one.

        :return list[(str, int|None)]: A list of files that failed to download.
        Each element of the list is a tuple where the first element
        is the file url and the second element is the status code that
        was returned from requests. If the download failed without a status code,
        this element will be None."""
        failures = []
        bar = ProgBar(len(urls))
        bar.counter = 1
        dst = Path(dst)
        dst.mkdir(parents=True, exist_ok=True)
        for url in urls:
            bar.display(prefix=f"Downloading file {bar.counter}/{bar.total}")
            headers = {"User-Agent": get_agent()}
            if extra_headers:
                headers |= extra_headers
            try:
                response = requests.get(url, headers=headers)
            except Exception as e:
                failures.append((url, None))
                continue
            if response.status_code != 200:
                failures.append((url, response.status_code))
                continue
            filename = Path(urlparse(url).path).name
            if Path(filename).suffix == "":
                filename += missing_ext_sub
            filepath = dst / filename
            if filepath.exists():
                filepath = filepath.with_stem(filepath.stem + str(time.time()))
            filepath.write_bytes(response.content)
        return failures

    def download_all(
        self,
        dst: Path | str,
        extra_headers: dict = None,
        missing_ext_subs: tuple[str] = (".jpg", ".mp4", ".mp3"),
    ) -> dict[str, list[tuple[str, int | None]]]:
        """Download all scraped files.

        :param dst: The destination folder to save to.
        Separate subfolders for images, videos, and audio
        will be created.

        :param extra_headers: Any additional headers
        to be added to the request.

        :param missing_ext_subs: A three-tuple of file extensions to use for
        the saved file if the url doesn't have one.
        The expected order is (image_ext, video_ext, audio_ext)

        :return dict[str, list[tuple[str, int | None]]]: Returns files
        that failed to download. The keys are "images", "videos", and "audio".
        The values are a list of tuples where the first element
        is the file url and the second element is the status code that
        was returned from requests. If the download failed without a status code,
        this element will be None.
        """
        link_types = ["images", "videos", "audio"]
        dst = Path(dst)
        subdirs = [dst / link_type for link_type in link_types]
        failures = {}
        for urls, subdir, ext_sub, link_type in zip(
            (self.image_urls, self.video_urls, self.audio_urls),
            subdirs,
            missing_ext_subs,
            link_types,
        ):
            fails = self.download_files(urls, subdir, extra_headers, ext_sub)
            if len(fails) > 0:
                failures[link_type] = fails
        # Remove empty subdir
        for subdir in subdirs:
            try:
                subdir.rmdir()
            except Exception as e:
                ...
        return failures


class PixelRipperSelenium(PixelRipper):
    def __init__(self, headless: bool = True, browser: str = "firefox"):
        super().__init__()
        self.user = User(headless=headless, browser_type=browser)

    def get(self, url: str, *args, **kwargs) -> requests.Response:
        """Get webpage using selenium.

        :param url: The url to scrape for media content.

        :return: A pseudo requests.Response
        object that only has "text" and "url"
        members."""
        try:
            if not self.user.browser_open:
                self.user.open_browser()
            self.user.get(url)
            time.sleep(1)
            old_scroll_height = self.user.script("return document.body.scrollHeight;")
            # Try to scroll to bottom of continously loading page style
            while True:
                self.user.scroll(fraction=1)
                time.sleep(1)
                if (
                    self.user.script("return document.body.scrollHeight;")
                    == old_scroll_height
                ):
                    break
                old_scroll_height = self.user.script(
                    "return document.body.scrollHeight;"
                )
            time.sleep(1)

            class Response:
                def __init__(self, text: str, url: str):
                    self.text = text
                    self.url = url

            return Response(self.user.browser.page_source, url)
        except Exception as e:
            print(e)
        finally:
            self.user.close_browser()


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument("url", type=str, help=""" The url to scrape for media. """)

    parser.add_argument(
        "-s",
        "--selenium",
        action="store_true",
        help=""" Use selenium to get page content
        instead of requests. """,
    )

    parser.add_argument(
        "-nh",
        "--no_headless",
        action="store_true",
        help="Don't use headless mode when using -s/--selenium. ",
    )

    parser.add_argument(
        "-b",
        "--browser",
        default="firefox",
        type=str,
        help=""" The browser to use when using -s/--selenium.
        Can be 'firefox' or 'chrome'. You must have the appropriate webdriver
        installed for your machine and browser version in order to use the selenium engine.""",
    )

    parser.add_argument(
        "-o",
        "--output_path",
        type=str,
        default=None,
        help=""" Output directory to save results to.
        If not specified, a folder with the name of the
        webpage will be created in the current working directory.""",
    )

    parser.add_argument(
        "-eh",
        "--extra_headers",
        nargs="*",
        type=str,
        default=[],
        help=""" Extra headers to use when requesting files as key, value pairs.
        Keys and values whould be colon separated and pairs should be space separated.
        e.g. -eh Referer:website.com/page Host:website.com""",
    )

    args = parser.parse_args()

    if not args.output_path:
        args.output_path = Path.cwd() / urlparse(args.url).netloc.strip("www.")
    else:
        args.output_path = Path(args.output_path).resolve()
    args.browser = args.browser.lower()
    if args.extra_headers:
        args.extra_headers = {
            pair[: pair.find(":")]: pair[pair.find(":") + 1 :]
            for pair in args.extra_headers
        }
    return args


def main(args: argparse.Namespace = None):
    if not args:
        args = get_args()
    ripper = (
        PixelRipperSelenium(not args.no_headless, args.browser)
        if args.selenium
        else PixelRipper()
    )
    ripper.rip(args.url)
    failures = ripper.download_all(args.output_path, extra_headers=args.extra_headers)
    if len(failures) > 0:
        print("Failed to download the following:")
        for key in failures:
            if len(failures[key]) > 0:
                print(f"{key}:")
                print(*failures[key], sep="\n")


if __name__ == "__main__":
    main(get_args())
