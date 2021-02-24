import json
from .utils import suppress_warnings  # don't remove: suppresses bad warnings from PushShiftAPI
from .utils import gen_slices, localtime
from warnings import warn
from psaw import PushshiftAPI
from praw import Reddit
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from abc import ABC, abstractmethod
from os.path import isfile


class Submissions(ABC):

    @abstractmethod
    def __init__(self, sub, proxies, valid_subreddit_dict=None):
        self.proxy_list = proxies.proxy_list

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
    def get_subreddit_submissions(self, start, end, subreddit, search_filter, sanity=False):
        pass

    @staticmethod
    def get_praw_credentials(filename):
        if not isfile(filename):
            raise ValueError("Invalid filename: {}".format(filename))
        credentials_dict = json.load(open(filename, 'r'))
        client_id = credentials_dict.get("client_id", None)
        client_secret = credentials_dict.get("client_secret", None)
        user_agent = credentials_dict.get("user_agent", None)
        return client_id, client_secret, user_agent

    @staticmethod
    def check_data_gaps(subreddit, start, end, results, sanity=False):
        if sanity:
            s, e = localtime(start), localtime(end)
            end_gap = (end - results[0]['created_utc']) / 60
            start_gap = (results[-1]['created_utc'] - start) / 60
            if end_gap > 20:
                warn("{}: No data for last {:.1f} minutes. Interval: {} to {}.".format(subreddit, end_gap, s, e))
            if start_gap > 20:
                warn("{}: No data for first {:.1f} minutes. Interval: {} to {}.".format(subreddit, start_gap, s, e))

            # timestamp of all created_utc + start and end of time interval
            timestamps = [end] + [result['created_utc'] for result in results] + [start]
            ts_diff = [(timestamps[i] - timestamps[i + 1]) / 60 for i in range(len(timestamps) - 1)]

            # index and value of max time gap
            i, m = max(enumerate(ts_diff), key=lambda x: x[1])

            # local time for start of gap and end of gap
            sg, eg = localtime(timestamps[i]), localtime(timestamps[i + 1])

            if m > 30:
                warn("{}: {:.1f} minute gap between {} and {}. Interval: {} to {}.".format(subreddit, m, sg, eg, s, e))

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

    def __init__(self, sub, proxies, valid_subreddit_dict=None):
        super().__init__(sub, proxies, valid_subreddit_dict)
        self.api_list = [PushshiftAPI(https_proxy=proxy) for proxy in self.proxy_list]

    def get_subreddit_submissions(self, start, end, subreddit, search_filter, sanity=False):
        # what search_submission argument would be if multi-threading not performed
        arg_dict = {'after': start, 'before': end, 'subreddit': subreddit, 'filter': search_filter}

        # generate time-sliced arguments
        arg_dict_list = gen_slices(len(self.proxy_list), arg_dict)

        # get generators that perform pushshift requests for their respective slices (using their respective proxies)
        generator_list = [self.api_list[i].search_submissions(**arg_dict_list[i]) for i in range(len(self.proxy_list))]

        # traverse the generators, each in their own thread; flatten to a list; convert each submission to a dictionary
        results = [submission.d_ for result in self._map(list, generator_list) for submission in result]

        # sanity check that data complete
        self.check_data_gaps(subreddit, start, end, results, sanity=False)

        return results


class SubmissionsPraw(Submissions):

    def __init__(self, sub, credentials_file, proxies, valid_subreddit_dict=None):
        super().__init__(sub, proxies, valid_subreddit_dict)

        client_id, client_secret, user_agent = self.get_praw_credentials(credentials_file)
        self.api_list = [Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent)]

    def get_subreddit_submissions(self, start, end, subreddit, search_filter, sanity=False):
        api = self.api_list[0]
        subreddit_api = api.subreddit(subreddit)

        if 'created_utc' not in search_filter:
            search_filter.append('created_utc')

        # praw limitation gets only 1000 posts
        results = []
        for submission in subreddit_api.new(limit=1000):
            if start <= submission.created_utc <= end:
                results.append({key: vars(submission)[key] for key in search_filter})

        # sanity check that data complete
        self.check_data_gaps(subreddit, start, end, results, sanity=False)

        return results


class SubmissionsHybrid(Submissions):

    def __init__(self, sub, credentials_file, proxies, valid_subreddit_dict=None):
        super().__init__(sub, proxies, valid_subreddit_dict)

        cid, cs, ua = self.get_praw_credentials(credentials_file)
        self.praw_api_list = [Reddit(client_id=cid, client_secret=cs, user_agent=ua) for i in self.proxy_list]
        self.api_list = [PushshiftAPI(r=self.praw_api_list[i], https_proxy=p) for i, p in enumerate(self.proxy_list)]

    def get_subreddit_submissions(self, start, end, subreddit, search_filter, sanity=False):

        ts_now = int(datetime.today().timestamp())

        # what search_submission argument would be if multi-threading not performed
        arg_dict = {'after': start, 'before': end, 'subreddit': subreddit, 'filter': search_filter}

        # generate time-sliced arguments
        arg_dict_list = gen_slices(len(self.proxy_list), arg_dict)

        # get generators that perform pushshift requests for their respective slices (using their respective proxies)
        generator_list = [self.api_list[i].search_submissions(**arg_dict_list[i]) for i in range(len(self.proxy_list))]

        # traverse the generators, each in their own thread; flatten to a list
        submissions = [submission for result in self._map(list, generator_list) for submission in result]

        if 'created_utc' not in search_filter:
            search_filter.append('created_utc')

        # convert submission objects to dictionaries
        results = [{key: vars(submission)[key] for key in search_filter} for submission in submissions]
        s, e = localtime(start), localtime(end)
        if not results:
            latest = start
            #warn("{}: no psaw results for interval {} to {}; using praw only".format(subreddit, s, e))
        else:
            latest = results[0]['created_utc']

        # add newer reddit posts from praw, in case psaw delayed
        if ts_now - end < 600:
            subreddit_api = self.praw_api_list[0].subreddit(subreddit)
            praw_submissions = list(subreddit_api.new(limit=100))
            if praw_submissions[-1].created_utc > latest:
                praw_submissions = list(subreddit_api.new(limit=1000))
            newest_praw = praw_submissions[0].created_utc
            if newest_praw > latest:
                oldest_newer_praw = next(x.created_utc for x in reversed(praw_submissions) if x.created_utc > latest)
                delay = (ts_now - oldest_newer_praw) / 60 / 60
                if delay > 2:
                    warn("{}: psaw delayed by more than {:.1f} hours".format(subreddit, delay))
            if praw_submissions[-1].created_utc > latest:
                # raise Exception("{}: psaw incomplete; delayed by more than {:.1f} hours".format(subreddit, delay))
                warn("{}: missing data from {} to {}".format(subreddit, s, localtime(praw_submissions[-1].created_utc)))
            praw_results = []
            for submission in praw_submissions:
                if latest < submission.created_utc <= end:
                    praw_results.append({key: vars(submission)[key] for key in search_filter})
                elif submission.created_utc <= latest:
                    break
            results = praw_results + results

        # sanity check that data complete
        self.check_data_gaps(subreddit, start, end, results, sanity=False)

        return results
