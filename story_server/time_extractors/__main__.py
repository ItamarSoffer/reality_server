import requests
import json
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup


"""
The class is build for extracting the date and time from links.
__init__ will contains the link, username and password- for handling authentications.
extract() will return a dict of {date: __, time: __} if success, and none if not.

the parser functions returns a single datetime object, and the _return_dict will rearrange it.

FORMATS: 
date: YYYY-mm-DD
time: HH:MM:SS
"""


class TimeExtract(object):
    def __init__(self, link, username, password):
        """

        :param link: The link to extract the time from
        :param username: user's username
        :param password: user's password
        """

        self.link = link
        self.username = username
        self.password = password

    def extract(self):
        pattern_parsers_dict = {".*www.ynet.co.il/articles/.*": self.ynet_parser}
        for regex_pattern, extract_function in pattern_parsers_dict.items():
            if re.findall(regex_pattern, self.link):
                # print("RUNS ON {}".format(self.url))
                # print("MATCHES REGEX: {}".format(regex_pattern))
                return extract_function()
        return None

    def ynet_parser(self):
        res = requests.get(self.link)
        soup = BeautifulSoup(res.text, "html.parser")
        list_of_scripts = soup.findAll("script")
        for script_data in list_of_scripts:
            try:
                content = script_data.contents[0]
                parsed_data = json.loads(content)
                date = datetime.strptime(parsed_data['datePublished'], '%Y-%m-%dT%H:%M:%Sz')
                date = date - timedelta(hours=3)
                return TimeExtract._return_dict(date)
            except Exception as e:
                print(e)
                pass
        return None

    @staticmethod
    def _return_dict(datetime_obj):
        """
        separate the datetime to date and time
        :param datetime_obj:
        :type datetime_obj: datetime
        :return:
        """
        return {
            "date": str(datetime_obj.date()),
            "time": str(datetime_obj.time()),
            "datetime": str(datetime_obj)
        }