#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" AutoDD: Automatically does the so called Due Diligence for you. """
import argparse
import pandas as pd
from warnings import warn
from time import time
from datetime import datetime, timedelta
from autodd.Proxies import Proxies
from autodd.Financials import Financials
from autodd.Submissions import SubmissionsPsaw, SubmissionsPraw, SubmissionsHybrid
from autodd.scores import get_ticker_scores, gen_delta_df, filter_df, print_df


def gen_dd_table():
    # Instantiate the parser
    parser = argparse.ArgumentParser(description='AutoDD Optional Parameters')

    parser.add_argument('--interval', nargs='?', const=24, type=int, default=24,
                        help='Choose an interval in hours to filter the results, default is 24 hours.')

    parser.add_argument('--sub', nargs='?', type=str, default='',
                        help='Choose a subreddit to scrape for tickers. If none provided all subs are searched.')

    parser.add_argument('--min', nargs='?', const=200, type=int, default=200,
                        help='Filter out results that have less than the min score, default is 200.')

    parser.add_argument('--maxprice', nargs='?', const=9999999, type=int, default=9999999,
                        help='Filter out results more than the max price set, default is 9999999.')

    parser.add_argument('--advanced', default=False, action='store_true',
                        help='Using this parameter shows advanced yahoo finance information on the ticker.')

    parser.add_argument('--sort', nargs='?', const=1, type=int, default=1,
                        help='Sort output by descending order of 1: total score, 2: recent score, 3: previous score, '
                        '4: change in score, 5: # of rocket emojis.')

    parser.add_argument('--db', default='hybrid', type=str,
                        help='Select database api: psaw (push-shift wrappers), praw (reddit api wrapper), or hybrid.')

    parser.add_argument('--no-threads', action='store_false', dest='threads',
                        help='Disable threading (enabled by default). Multi-tasking speeds up downloading of data.')

    parser.add_argument('--csv', default=False, action='store_true',
                        help='Using this parameter produces a autodd.csv file, rather than a .txt file.')

    parser.add_argument('--filename', nargs='?', const='autodd', type=str, default='autodd',
                        help='Set output filename. ".csv" or ".txt" appended depending if the --csv option is used.')

    parser.add_argument('--proxy_file', nargs='?', type=str, default=None,
                        help='Optionally provide a file containing proxies to speed up reddit retrieval.')

    parser.add_argument('--cred_file', nargs='?', type=str, default=None,
                        help='Provide a file containing praw credentials. Required if db=praw or db=hybrid.')

    start = time()

    args = parser.parse_args()

    # get a list of proxies from proxy file
    proxies = Proxies(args.proxy_file)

    print("Getting submissions and generating scores dataframe...")

    # get submissions and computer scores
    recent, prev = get_submissions(args.interval, args.sub, args.db, proxies, args.cred_file)

    current_scores_df, current_rockets_df = get_ticker_scores(recent, ['🚀'])
    prev_scores_df, prev_rockets_df = get_ticker_scores(prev, ['🚀'])

    # populate score dataframe
    results_df = gen_delta_df(current_scores_df, prev_scores_df, args.interval)
    if len(current_scores_df) > 1:
        totals = current_scores_df.add(prev_scores_df, fill_value=0).astype('int32')
        results_df = pd.concat([results_df, totals], axis=1)

    results_df = filter_df(results_df, args.min)

    # count rockets
    rockets_df = current_rockets_df.add(prev_rockets_df, fill_value=0).astype('int32')
    results_df.insert(loc=4, column='Rockets', value=rockets_df)
    results_df = results_df.fillna(value=0)

    print("Getting financial stats...")
    financials = Financials(threads=args.threads)
    results_df = financials.get_financial_stats(results_df, args.advanced)

    # Sort by Total (sort = 1), Recent ( = 2), Prev ( = 3), Change ( = 4), Rockets ( = 5)
    results_df.sort_values(by=results_df.columns[args.sort - 1], inplace=True, ascending=False)

    print_df(results_df, 'output\\' + args.filename, args.csv)
    total_time = str(timedelta(seconds=round(time() - start)))
    print("AutoDD took " + total_time + " (H:MM:SS).")
    print("Dataframe has {} rows".format(len(results_df.index)))


def get_submissions(n, sub, db='psaw', proxies=None, praw_cred_file=None):
    """
    Returns two dictionaries:
    1st dictionary: current result from n hours ago until now
    2nd dictionary: prev result from 2n hours ago until n hours ago
    The two dictionaries' keys are the requested subreddit: all subreddits if allsub is True, and just "sub" otherwise
    The value paired with each subreddit key is a generator which traverses each submission
     """

    if db == 'psaw':
        submissions_api = SubmissionsPsaw(sub=sub, proxies=proxies)
    elif db == 'praw':
        submissions_api = SubmissionsPraw(sub=sub, credentials_file=praw_cred_file, proxies=proxies)
    elif db == 'hybrid':
        submissions_api = SubmissionsHybrid(sub=sub, credentials_file=praw_cred_file, proxies=proxies)
    else:
        raise ValueError("Invalid db '{}'. Valid choices:\npsaw, praw, hybrid".format(db))

    mid_interval = datetime.today() - timedelta(hours=n)
    ts_mid = int(mid_interval.timestamp())
    ts_start = int((mid_interval - timedelta(hours=n)).timestamp())
    ts_end = int(datetime.today().timestamp())

    search_filter = ['title', 'link_flair_text', 'selftext', 'score']
    sanity = ['wallstreetbets', 'wallstreetbetsELITE', 'SatoshiStreetBets']
    recent = submissions_api.get_submissions(start=ts_mid, end=ts_end, search_filter=search_filter,
                                             sanity_list=sanity)
    prev = submissions_api.get_submissions(start=ts_start, end=ts_mid, search_filter=search_filter,
                                           sanity_list=sanity)

    if all(value == [] for value in prev.values()):
        raise Exception('No results for the previous time period.')
    elif not recent:
        raise Exception('No results for the recent time period.')

    for subreddit in prev:
        if not prev[subreddit]:
            warn('No results for the previous time period in {} subreddit.'.format(subreddit))
        if not recent[subreddit]:
            warn('No results for the recent time period in {} subreddit.'.format(subreddit))

    return recent, prev

if __name__ == '__main__':
    gen_dd_table()
