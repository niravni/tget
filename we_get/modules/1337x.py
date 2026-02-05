"""
Copyright (c) 2016-2020 we-get developers (https://github.com/rachmadaniHaryono/we-get/)
See the file 'LICENSE' for copying permission
"""

from urllib.parse import quote_plus
from we_get.core.module import Module
import re
import requests

BASE_URL = "https://1337x.st"
SEARCH_LOC = "/search/%s/1/"
LIST_LOC = "/top-100"


class leetx(object):
    """ 1337x module for we-get.
    """

    def __init__(self, pargs):
        self.links = None
        self.pargs = pargs
        self.action = None
        self.search_query = None
        self.module = Module()
        self.parse_pargs()
        self.items = dict()
        self.results = 10  # Limit the results to avoid blocking.

    def parse_pargs(self):
        for opt in self.pargs:
            if opt == "--search":
                self.action = "search"
                self.search_query = self.pargs[opt][0]
            elif opt == "--list":
                self.action = "list"

    def set_item(self, link):
        url = "%s%s" % (BASE_URL, link)
        magnet = None
        item = dict()
        
        try:
            data = self.module.http_get_request(url)
            # Try multiple patterns for magnet links
            # Pattern 1: Standard href with magnet
            magnet_links = re.findall(r'href=[\'"]?(magnet:[^\'">]+)', data, re.IGNORECASE)
            # Pattern 2: Direct magnet links in data
            if not magnet_links:
                magnet_links = re.findall(r'(magnet:\?[^\'"\s<>]+)', data, re.IGNORECASE)
            
            # Try multiple patterns for seeders/leechers as site structure may vary
            seeders = '0'
            leechers = '0'
            
            # Pattern 1: Standard span with class="seeds"
            seeders_match = re.findall(r'<span[^>]*class=["\']seeds["\'][^>]*>(.*?)</span>', data, re.IGNORECASE | re.DOTALL)
            if not seeders_match:
                # Pattern 2: Alternative format
                seeders_match = re.findall(r'<span class=["\']seeds["\']>(.*?)</span>', data, re.IGNORECASE)
            if not seeders_match:
                # Pattern 3: Generic seeds text
                seeders_match = re.findall(r'>Seeds?[:\s]*(\d+)', data, re.IGNORECASE)
            if seeders_match:
                seeders = seeders_match[0].strip()
            
            # Pattern 1: Standard span with class="leeches"
            leechers_match = re.findall(r'<span[^>]*class=["\']leeches["\'][^>]*>(.*?)</span>', data, re.IGNORECASE | re.DOTALL)
            if not leechers_match:
                # Pattern 2: Alternative format
                leechers_match = re.findall(r'<span class=["\']leeches["\']>(.*?)</span>', data, re.IGNORECASE)
            if not leechers_match:
                # Pattern 3: Generic leechers text
                leechers_match = re.findall(r'>Leech(?:ers?)?[:\s]*(\d+)', data, re.IGNORECASE)
            if leechers_match:
                leechers = leechers_match[0].strip()
            
            # Get magnet link
            if magnet_links:
                magnet = magnet_links[0]
            
            if not magnet:
                return item
                
            try:
                name = self.module.fix_name(self.module.magnet2name(magnet))
                item.update(
                    {name: {'seeds': seeders, 'leeches': leechers, 'link': magnet}}
                )
            except (IndexError, AttributeError, ValueError) as e:
                # If magnet parsing fails, try to extract name from page title or other sources
                try:
                    # Fallback: try to get name from page
                    title_match = re.findall(r'<title[^>]*>(.*?)</title>', data, re.IGNORECASE | re.DOTALL)
                    if title_match:
                        name = self.module.fix_name(title_match[0].split('|')[0].strip())
                        item.update(
                            {name: {'seeds': seeders, 'leeches': leechers, 'link': magnet}}
                        )
                except Exception:
                    pass
        except requests.exceptions.Timeout:
            pass
        except Exception:
            pass
        return item

    def search(self):
        url = "%s%s" % (BASE_URL, SEARCH_LOC % (quote_plus(self.search_query)))
        try:
            data = self.module.http_get_request(url)
            # Try multiple patterns for finding torrent links
            # Pattern 1: Standard href links
            links = re.findall(r'href=[\'"]?([^\'">]+)', data)
            # Pattern 2: More specific torrent page links
            torrent_links = re.findall(r'href=[\'"]?([^\'">]*torrent/[^\'">]+)', data, re.IGNORECASE)
            
            # Use the more specific pattern if available, otherwise fall back to general
            if torrent_links:
                links = torrent_links
            else:
                # Filter to only torrent links
                links = [link for link in links if "/torrent/" in link]
            
            results = 0
            seen_links = set()  # Avoid duplicate processing

            for link in links:
                if results == self.results:
                    break
                # Normalize link (remove leading slash if BASE_URL already has it)
                if link.startswith('/'):
                    full_link = link
                elif link.startswith('http'):
                    # Skip external links
                    continue
                else:
                    full_link = '/' + link
                
                # Skip if we've already processed this link
                if full_link in seen_links:
                    continue
                seen_links.add(full_link)
                
                if "/torrent/" in full_link:
                    try:
                        item = self.set_item(full_link)
                        if item:
                            self.items.update(item)
                            results += 1
                    except Exception:
                        # Skip this item and continue
                        continue
        except requests.exceptions.Timeout:
            pass
        except Exception:
            pass
        return self.items

    def list(self):
        url = "%s%s" % (BASE_URL, LIST_LOC)
        try:
            data = self.module.http_get_request(url)
            # Try multiple patterns for finding torrent links
            torrent_links = re.findall(r'href=[\'"]?([^\'">]*torrent/[^\'">]+)', data, re.IGNORECASE)
            if not torrent_links:
                links = re.findall(r'href=[\'"]?([^\'">]+)', data)
                links = [link for link in links if "/torrent/" in link]
            else:
                links = torrent_links
            
            results = 0
            seen_links = set()

            for link in links:
                if results == self.results:
                    break
                # Normalize link
                if link.startswith('/'):
                    full_link = link
                elif link.startswith('http'):
                    continue
                else:
                    full_link = '/' + link
                
                if full_link in seen_links:
                    continue
                seen_links.add(full_link)
                
                if "/torrent/" in full_link:
                    try:
                        item = self.set_item(full_link)
                        if item:
                            self.items.update(item)
                            results += 1
                    except Exception:
                        continue
        except requests.exceptions.Timeout:
            pass
        except Exception:
            pass
        return self.items


def main(pargs):
    run = leetx(pargs)
    if run.action == "list":
        return run.list()
    elif run.action == "search":
        return run.search()
