from concurrent.futures import ThreadPoolExecutor, as_completed
from utils import *
from psaw import PushshiftAPI as psaw_api
from pmaw import PushshiftAPI as pmaw_api
import praw
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

class Submissions(ABC):

    @abstractmethod
    def __init__(self, proxy_list, sub=None, valid_subreddit_dict=None):
        self.proxy_list = proxy_list

        if not valid_subreddit_dict:
            valid_subreddit_dict = {'pennystocks': 'pnnystks',
                              'RobinHoodPennyStocks': 'RHPnnyStck',
                              'Daytrading': 'daytrade',
                              'StockMarket': 'stkmrkt',
                              'stocks': 'stocks',
                              'investing': 'investng',
                              'wallstreetbets': 'WSB'}

        if sub:
            if sub not in valid_subreddit_dict:
                choices_str = ', '.join(list(valid_subreddit_dict.keys()))
                raise ValueError("Invalid subreddit '{}'. Valid choices:\n{}".format(sub, choices_str))
            else:
                self.subreddit_dict = {sub: valid_subreddit_dict[sub]}
        else:
            self.subreddit_dict = valid_subreddit_dict

        self.executor = ThreadPoolExecutor(max_workers=len(self.proxy_list))

    @abstractmethod
    def get_subreddit_submissions(self, after, before, subreddit, search_filter):
        pass

    def get_submissions(self, n):
        """
        Returns a list of results for submission in past:
        1st list: current result from n hours ago until now
        2nd list: prev result from 2n hours ago until n hours ago
        """

        mid_interval = datetime.today() - timedelta(hours=n)
        timestamp_mid = int(mid_interval.timestamp())
        timestamp_start = int((mid_interval - timedelta(hours=n)).timestamp())
        timestamp_end = int(datetime.today().timestamp())

        recent = {}
        prev = {}
        search_filter = ['title', 'link_flair_text', 'selftext', 'score']
        for subreddit in self.subreddit_dict:
            recent[subreddit] = self.get_subreddit_submissions(timestamp_mid, timestamp_end, subreddit, search_filter)
            prev[subreddit] = self.get_subreddit_submissions(timestamp_start, timestamp_mid, subreddit, search_filter)

        return recent, prev

class SubmissionsPsaw(Submissions):

    def __init__(self, proxy_list, sub=None, valid_subreddit_dict=None):
        super().__init__(proxy_list, sub, valid_subreddit_dict)
        self.api_list = [psaw_api(https_proxy=proxy) for proxy in self.proxy_list]

    def get_subreddit_submissions(self, after, before, subreddit, search_filter):
        arg_dict = {'after': after, 'before': before, 'subreddit': subreddit, 'filter': search_filter}
        arg_dict_list = gen_payloads(len(self.proxy_list), arg_dict)
        generator_list = [self.api_list[i].search_submissions(**arg_dict_list[i]) for i in range(len(self.proxy_list))]
        futures = [self.executor.submit(list, generator_list[i]) for i in range(len(self.proxy_list))]
        results = [submission._asdict() for future in as_completed(futures) for submission in future.result()]
        return results

class SubmissionsPmaw(Submissions):

    def __init__(self, proxy_list, sub=None, valid_subreddit_dict=None):
        super().__init__(proxy_list, sub, valid_subreddit_dict)
        self.api_list = [pmaw_api(num_workers=2, https_proxy=proxy) for proxy in proxy_list]

    def get_subreddit_submissions(self, after, before, subreddit, search_filter):
        arg_dict = {'after': after, 'before': before, 'subreddit': subreddit, 'filter': search_filter}
        arg_dict_list = gen_payloads(len(self.proxy_list), arg_dict)
        futures = [self.executor.submit(self.api_list[i].search_submissions, **arg_dict_list[i])
                   for i in range(len(self.proxy_list))]
        results = [future.result() for future in as_completed(futures)]
        return results

class SubmissionsPraw(Submissions):

    def __init__(self, proxy_list, sub=None, valid_subreddit_dict=None):
        super().__init__(proxy_list, sub, valid_subreddit_dict)

        # praw credentials
        client_id = "3RbFQX8O9UqDCA"
        client_secret = "NalOX_ZQqGWP4eYKZv6bPlAb2aWOcA"
        user_agent = "subreddit_scraper"

        self.api_list = [praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent)]

    def get_subreddit_submissions(self, after, before, subreddit, search_filter):
        api = self.api_list[0]
        subreddit_api = api.subreddit(subreddit)

        # praw limitation gets only 1000 posts
        results = []
        for submission in subreddit_api.new(limit=1000):
            if submission.created_utc >= after and submission.created_utc <= before:
                results.append({key: vars(submission)[key] for key in search_filter})

        return results