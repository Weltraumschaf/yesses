import requests
import logging
from random import randint

from yesses.module import YModule, YExample
from yesses import utils

log = logging.getLogger('discover/error_paths')


class ErrorPaths(YModule):
    """
    Collect error pages to scan them for information leakages.
    """
    USER_AGENTS_LIST = "assets/user-agents.txt"

    INPUTS = {
        "origins": {
            "required_keys": [
                "ip",
                "domain",
                "url"
            ],
            "description": "Required. Origins to get error pages",
        },
    }

    OUTPUTS = {
        "Error-Pages": {
            "provided_keys": [
                "url",
                "header",
                "data"
            ],
            "description": "Error pages and the content from the page"
        }
    }

    def run(self):
        # read user agents list
        user_agents = utils.read_file(self.USER_AGENTS_LIST)

        if not user_agents:
            log.error("Could not open user agent list")
            return

        for origin in self.origins:
            with utils.force_ip_connection(origin['domain'], origin['ip']):
                parsed_url = utils.UrlParser(origin['url'])

                # get page with 404 not found error
                r = requests.get(f"{parsed_url.url_without_path}/fvwwvaoqgf/opdvsltqfnlcelh/ddsleo/glcgrfmr.odt",
                                 headers={'User-Agent': user_agents[randint(0, len(user_agents) - 1)]})
                parsed_url = utils.UrlParser(r.url)

                header_list = utils.convert_header(r)
                self.results['Error-Pages'].append(
                    {'url': parsed_url.full_url(), 'header': header_list, 'data': r.text})