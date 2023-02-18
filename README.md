# Pixelripper
Package and CLI for downloading media from a webpage. <br>
Install with:<br>
<pre>
pip install pixelripper
</pre>

Pixelripper contains a class called PixelRipper and a subclass called PixelRipperSelenium.<br>
PixelRipper uses the requests library to fetch webpages and PixelRipperSelenium uses a selenium based engine to do the same.<br>
The selenium engine is slower and requires more resources, but is useful for webpages
that don't render their media content without a JavaScript engine.<br>
It can use either Firefox or Chrome browsers.<br>
Note: You must have the appropriate webdriver for your machine and browser
version installed in order to use PixelRipperSelenium.<br>
pixelripper can be used programmatically or from the command line.<br>
<br>
### Programmatic usage:
<pre>
from pixelripper import PixelRipper
from pathlib import Path
ripper = PixelRipper()
# Scrape the page for image, video, and audio urls.
ripper.rip("https://somewebsite.com")
# Any content urls found will now be accessible as members of ripper.
print(ripper.image_urls)
print(ripper.video_urls)
print(ripper.audio_urls)
# All the urls found on a page can be accessed through the ripper.scraper member.
all_urls = ripper.scraper.get_links("all")
# The urls can also be filtered according to a list of extensions 
# with the filter_by_extensions function.
# The following will return only .jpg and .mp3 file urls.
urls = ripper.filter_by_extensions([".jpg", ".mp3"])
# The content can then be downloaded.
ripper.download_files(urls, Path.cwd()/"somewebsite")
# Alternatively, everything in ripper.image_urls, ripper.video_urls, and ripper.audio_urls
# can be downloaded with just a call to ripper.download_all()
ripper.download_all(Path.cwd()/"somewebsite")
# Separate subfolders named "images", "videos", and "audio"
# will be created inside the "somewebsite" folder when using this function.

</pre>
### Command line usage:
<pre>
>pixelripper -h
usage: pixelripper [-h] [-s] [-nh] [-b BROWSER] [-o OUTPUT_PATH] [-eh [EXTRA_HEADERS ...]] url

positional arguments:
  url                   The url to scrape for media.

options:
  -h, --help            show this help message and exit
  -s, --selenium        Use selenium to get page content instead of requests.
  -nh, --no_headless    Don't use headless mode when using -s/--selenium.
  -b BROWSER, --browser BROWSER
                        The browser to use when using -s/--selenium. Can be 'firefox' or 'chrome'. You must have the appropriate webdriver installed for your machine and browser version in order to use the selenium engine.
  -o OUTPUT_PATH, --output_path OUTPUT_PATH
                        Output directory to save results to. If not specified, a folder with the name of the webpage will be created in the current working directory.
  -eh [EXTRA_HEADERS ...], --extra_headers [EXTRA_HEADERS ...]
                        Extra headers to use when requesting files as key, value pairs. Keys and values whould be colon separated and pairs should be space separated. e.g. -eh Referer:website.com/page Host:website.com
</pre>