from concurrent.futures import ThreadPoolExecutor
import utils
from psaw import PushshiftAPI as psaw_api
from warnings import warn, catch_warnings
from praw import Reddit
import json
from datetime import datetime
from abc import ABC, abstractmethod
from os.path import isfile

class Submissions(ABC):

    @abstractmethod
    def __init__(self, proxy_list, sub=None, valid_subreddit_dict=None):
        self.proxy_list = proxy_list

        if not valid_subreddit_dict:
            valid_subreddit_dict = {'wallstreetbets': 'WSB',
                              'wallstreetbetsELITE': 'WallStreetbetsELITE',
                              'stocks': 'stocks',
                              'investing': 'investng',
                              'SatoshiStreetBets': 'SatoshiStreetBets',
                              'pennystocks': 'pnnystks',
                              'RobinHoodPennyStocks': 'RHPnnyStck',
                              'StockMarket': 'stkmrkt',
                              'Daytrading': 'daytrade',
                              }

        if sub:
            if sub not in valid_subreddit_dict:
                choices_str = ', '.join(list(valid_subreddit_dict.keys()))
                raise ValueError("Invalid subreddit '{}'. Valid choices:\n{}".format(sub, choices_str))
            else:
                self.subreddit_dict = {sub: valid_subreddit_dict[sub]}
        else:
            self.subreddit_dict = valid_subreddit_dict

        self.executor = ThreadPoolExecutor(max_workers=len(self.proxy_list))
        self._map = self.executor.map

    @abstractmethod
    def get_subreddit_submissions(self, start, end, subreddit, search_filter):
        pass

    def get_praw_credentials(self, filename):
        if not isfile(filename):
            raise ValueError("Invalid filename: {}".format(filename))
        credentials_dict = json.load(open(filename, 'r'))
        client_id = credentials_dict.get("client_id", None)
        client_secret = credentials_dict.get("client_secret", None)
        user_agent = credentials_dict.get("user_agent", None)
        return client_id, client_secret, user_agent

    def get_submissions(self, start, end, search_filter, sanity_list=[]):
        """
        Returns a list of submissions between start and end, and satisfying criteria in search_filter
        """
        results = {}
        for subreddit in self.subreddit_dict:
            sanity = False
            if subreddit in sanity_list:
                sanity = True
            results[subreddit] = self.get_subreddit_submissions(start, end, subreddit, search_filter, sanity)

        return results

class SubmissionsPsaw(Submissions):

    def __init__(self, sub, proxy_list, valid_subreddit_dict=None):
        super().__init__(proxy_list, sub, valid_subreddit_dict)
        self.api_list = [psaw_api(https_proxy=proxy) for proxy in self.proxy_list]

    def get_subreddit_submissions(self, start, end, subreddit, search_filter):
        # what search_submission argument would be if multi-threading not performed
        arg_dict = {'after': start, 'before': end, 'subreddit': subreddit, 'filter': search_filter}

        # generate time-sliced arguments
        arg_dict_list = utils.gen_slices(len(self.proxy_list), arg_dict)

        # get generators that perform pushshift requests for their respective slices (using their respective proxies)
        generator_list = [self.api_list[i].search_submissions(**arg_dict_list[i]) for i in range(len(self.proxy_list))]

        # traverse the generators, each in their own thread; flatten to a list; convert each submission to a dictionary
        with catch_warnings():
            results = [submission.d_ for result in self._map(list, generator_list) for submission in result]
        return results

class SubmissionsPraw(Submissions):

    def __init__(self, sub, credentials_file, proxy_list, valid_subreddit_dict=None):
        super().__init__(proxy_list, sub, valid_subreddit_dict)

        client_id, client_secret, user_agent = self.get_praw_credentials(credentials_file)
        self.api_list = [Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent)]

    def get_subreddit_submissions(self, start, end, subreddit, search_filter):
        api = self.api_list[0]
        subreddit_api = api.subreddit(subreddit)

        if 'created_utc' not in search_filter:
            search_filter.append('created_utc')

        # praw limitation gets only 1000 posts
        results = []
        for submission in subreddit_api.new(limit=1000):
            if submission.created_utc >= start and submission.created_utc <= end:
                results.append({key: vars(submission)[key] for key in search_filter})

        return results

class SubmissionsHybrid(Submissions):

    def __init__(self, sub, credentials_file, proxy_list, valid_subreddit_dict=None):
        super().__init__(proxy_list, sub, valid_subreddit_dict)

        cid, cs, ua = self.get_praw_credentials(credentials_file)
        self.praw_api_list = [Reddit(client_id=cid, client_secret=cs, user_agent=ua) for i in self.proxy_list]
        self.api_list = [psaw_api(r=self.praw_api_list[i], https_proxy=p) for i, p in enumerate(self.proxy_list)]

    def get_subreddit_submissions(self, start, end, subreddit, search_filter, sanity=False):

        # what search_submission argument would be if multi-threading not performed
        arg_dict = {'after': start, 'before': end, 'subreddit': subreddit, 'filter': search_filter}

        # generate time-sliced arguments
        arg_dict_list = utils.gen_slices(len(self.proxy_list), arg_dict)

        # get generators that perform pushshift requests for their respective slices (using their respective proxies)
        generator_list = [self.api_list[i].search_submissions(**arg_dict_list[i]) for i in range(len(self.proxy_list))]

        # traverse the generators, each in their own thread; flatten to a list
        with catch_warnings():
            submissions = [submission for result in self._map(list, generator_list) for submission in result]

        if 'created_utc' not in search_filter:
            search_filter.append('created_utc')

        # convert submission objects to dictionaries
        results = [{key: vars(submission)[key] for key in search_filter} for submission in submissions]
        latest_psaw_utc = results[0]['created_utc']

        # add any reddit posts that occurred in past 10mins, in case psaw delayed
        ts_now = int(datetime.today().timestamp())
        if ts_now - end < 600:
            subreddit_api = self.praw_api_list[0].subreddit(subreddit)
            praw_results = []
            for submission in subreddit_api.new(limit=100):
                if latest_psaw_utc < submission.created_utc <= end:
                    praw_results.append({key: vars(submission)[key] for key in search_filter})
                elif submission.created_utc <= latest_psaw_utc:
                    break
            if submission.created_utc > latest_psaw_utc:
                psaw_delay_min = (ts_now - submission.created_utc) / 60
                raise Exception("psaw delayed by more than {0:.1f} minutes".format(psaw_delay_min))
            results = praw_results + results

        # sanity check that data complete
        if sanity:
            end_gap = (end - results[0]['created_utc']) / 60
            if end_gap > 20:
                s, e = utils.localtime(start), utils.localtime(end)
                warn("{}: No data for last {:.1f} minutes. Interval: {} to {}.".format(subreddit, end_gap, s, e))

        return results
