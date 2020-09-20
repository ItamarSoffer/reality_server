import requests
import json
import re
from datetime import datetime
from bs4 import BeautifulSoup

"""
Each parse function needs to return a dict in the following structure:
'type'- string, the parser name
'color' - string- the card color
'content' - dict- any parsed content. 
"""


class HtmlParser(object):
    """
    each of the functions will be an HTML parser.
    if the function works, it will return a dict of the parsed data
    if not, returns None.

    The init function will match the relevant parser by regex of the url
    """
    PARSERS_PARAMS = {'ynet': ['ynet', '#ff0000'],
                      'iframe': ['iframe', '#bfbfbf'],
                      'splunk': ['splunk', '#ff7a45'],
                      }

    def __init__(self, url, username):
        """
        each function will download the data, some will need GET and some POST.
        :param url:
        """
        self.url = url
        self.username = username
        self.content = None
        # self.match_parser()
        # parse by functions

    def match_parser(self):
        pattern_parsers_dict = {".*www.ynet.co.il/articles/.*": self.ynet_parser,
                                "<iframe .*></iframe>": self.iframe_parser}
        for regex_pattern, parse_function in pattern_parsers_dict.items():
            if re.findall(regex_pattern, self.url):
                # logging.info("RUNS ON {}".format(self.url))
                # logging.info("MATCHES REGEX: {}".format(regex_pattern))
                return parse_function()
        return None

    def iframe_parser(self):
        soup = BeautifulSoup(self.url, "html.parser")
        iframe = soup.find_all('iframe')[0]
        self.content = iframe.attrs
        return self._return_story_dict('iframe')


    def ynet_parser(self):
        res = requests.get(self.url)
        soup = BeautifulSoup(res.text, "html.parser")
        list_of_scripts = soup.findAll("script")
        for script_data in list_of_scripts:
            try:
                content = script_data.contents[0]
                parsed_data = json.loads(content)
                headline = parsed_data['headline']
                date = datetime.strptime(parsed_data['datePublished'], '%Y-%m-%dT%H:%M:%Sz')
                body = parsed_data['articleBody']
                self.content = {'datetime': date,
                                'title': headline,
                                'text': body}
                return self._return_story_dict('ynet')
            except Exception as e:
                pass
        return None

    def _return_story_dict(self, parser_name):
        """
        returns the dict for the story ExtraData component
        :param parser_name:
        :return:
        """
        if parser_name in self.PARSERS_PARAMS.keys():
            return {
                'type': self.PARSERS_PARAMS[parser_name][0],
                'color': self.PARSERS_PARAMS[parser_name][1],
                'content': self.content
            }



