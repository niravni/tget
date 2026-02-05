"""
Copyright (c) 2016-2020 we-get developers (https://github.com/rachmadaniHaryono/we-get/)
See the file 'LICENSE' for copying permission
"""

from we_get.core.module import Module
import json
import requests
import socket

BASE_URL = "https://yts.bz"


class yts(object):
    """ yts module using the JSON API.
    """

    def __init__(self, pargs):
        self.links = None
        self.pargs = pargs
        self.action = None
        self.quality = "720p"
        self.genre = "all"
        self.search_query = None
        self.module = Module()
        self.parse_pargs()
        self.items = dict()

    def parse_pargs(self):
        for opt in self.pargs:
            if opt == "--search":
                self.action = "search"
                # YTS API expects URL-encoded query, not dash-separated
                from urllib.parse import quote_plus
                self.search_query = quote_plus(self.pargs[opt][0])
            elif opt == "--list":
                self.action = "list"
            elif opt == "--quality":
                self.quality = self.pargs[opt][0]
            elif opt == "--genre":
                self.genre = self.pargs[opt][0]

    def search(self):
        # YTS API format: quality and genre need proper formatting
        quality_param = "&quality=%s" % self.quality if self.quality != "720p" else ""
        genre_param = "&genre=%s" % self.genre if self.genre != "all" else ""
        url = "%s/api/v2/list_movies.json?query_term=%s%s%s" % (
            BASE_URL,
            self.search_query,
            quality_param,
            genre_param
        )
        try:
            response = self.module.http_get_request(url)
            data = json.loads(response)
            try:
                api = data['data']['movies']
            except KeyError:
                return self.items
            for movie in api:
                if not movie.get('torrents') or len(movie['torrents']) == 0:
                    continue
                name = self.module.fix_name(movie['title'])
                seeds = movie['torrents'][0].get('seeds', '0')
                leeches = movie['torrents'][0].get('peers', '0')
                link = movie['torrents'][0].get('url', '')
                if link:
                    self.items.update({
                        name: {'seeds': str(seeds), 'leeches': str(leeches), 'link': link}
                    })
        except (json.decoder.JSONDecodeError, KeyError, IndexError):
            return self.items
        except (requests.exceptions.ConnectionError,
                requests.exceptions.RequestException,
                requests.exceptions.Timeout,
                socket.gaierror,
                socket.error):
            return self.items
        return self.items

    def list(self):
        # YTS API format: quality and genre need proper formatting
        params = []
        if self.quality != "720p":
            params.append("quality=%s" % self.quality)
        if self.genre != "all":
            params.append("genre=%s" % self.genre)
        param_string = "?" + "&".join(params) if params else ""
        url = "%s/api/v2/list_movies.json%s" % (BASE_URL, param_string)
        try:
            response = self.module.http_get_request(url)
            data = json.loads(response)
            try:
                api = data['data']['movies']
            except KeyError:
                return self.items
            for movie in api:
                if not movie.get('torrents') or len(movie['torrents']) == 0:
                    continue
                torrent_name = self.module.fix_name(movie['title'])
                seeds = movie['torrents'][0].get('seeds', '0')
                leeches = movie['torrents'][0].get('peers', '0')
                link = movie['torrents'][0].get('url', '')
                if link:
                    self.items.update({torrent_name: {'leeches': str(leeches),
                                                      'seeds': str(seeds), 'link': link}})
        except (json.decoder.JSONDecodeError, KeyError, IndexError):
            return self.items
        except (requests.exceptions.ConnectionError,
                requests.exceptions.RequestException,
                requests.exceptions.Timeout,
                socket.gaierror,
                socket.error):
            return self.items
        return self.items


def main(pargs):
    run = yts(pargs)
    if run.action == "list":
        return run.list()
    elif run.action == "search":
        return run.search()
