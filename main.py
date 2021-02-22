#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" AutoDD: Automatically does the so called Due Diligence for you. """
import argparse
import time
import utils
from collections import Counter
from AutoDD import *

def main():
    # Instantiate the parser
    parser = argparse.ArgumentParser(description='AutoDD Optional Parameters')

    parser.add_argument('--interval', nargs='?', const=24, type=int, default=24,
                    help='Choose an interval in hours to filter the results, default is 24 hours.')

    parser.add_argument('--sub', nargs='?', type=str, default='',
                    help='Choose a subreddit to scrape for tickers. If none provided all subs are searched.')

    parser.add_argument('--min', nargs='?', const=100, type=int, default=100,
                    help='Filter out results that have less than the min score, default is 100.')

    parser.add_argument('--maxprice', nargs='?', const=9999999, type=int, default=9999999,
                    help='Filter out results more than the max price set, default is 9999999.')

    parser.add_argument('--advanced', default=False, action='store_true',
                    help='Using this parameter shows advanced yahoo finance information on the ticker.')

    parser.add_argument('--sort', nargs='?', const=1, type=int, default=1,
                    help='Sort output by descending order of 1: total score, 2: recent score, 3: previous score, '
                         '4: change in score, 5: # of rocket emojis.')

    parser.add_argument('--db', default='hybrid', type=str,
                    help='Select the database api: psaw (push-shift wrappers), praw (reddit api wrapper), or hybrid.')

    parser.add_argument('--no-threads', action='store_false', dest='threads',
                    help='Disable multi-tasking (enabled by default). Multi-tasking speeds up downloading of data.')

    parser.add_argument('--csv', default=False, action='store_true',
                    help='Using this parameter produces a table_records.csv file, rather than a .txt file.')

    parser.add_argument('--filename', nargs='?', const='ticker_table', type=str, default='ticker_table',
                    help='Change the file name from table_records to whatever you wish.')

    parser.add_argument('--proxy_file', nargs='?', type=str, default=None,
                    help='Optionally provide a file containing proxies to speed up reddit retrieval.')

    parser.add_argument('--cred_file', nargs='?', type=str, default=None,
                    help='Provide a file containing praw credentials. Required if db=praw or db=hybrid.')


    start = time.time()

    args = parser.parse_args()

    # get a list of proxies from proxy file
    proxies = utils.get_proxies(args.proxy_file)

    print("Getting submissions...")
    recent, prev = get_submissions(args.interval, args.sub, args.db, proxies, args.cred_file)

    print("Searching for tickers...")
    current_scores, current_rocket_scores = get_ticker_scores(recent)
    prev_scores, prev_rocket_scores = get_ticker_scores(prev)

    print("Populating results...")
    results_df = score_change_df(current_scores, prev_scores, args.interval)
    results_df = filter_df(results_df, args.min)

    print("Counting rockets...")
    rockets = Counter(current_rocket_scores) + Counter(prev_rocket_scores)
    results_df.insert(loc=4, column='Rockets', value=pd.Series(rockets, dtype='int32'))
    results_df = results_df.fillna(value=0).astype({'Rockets': 'int32'})

    print("Getting financial stats...")
    results_df = get_financial_stats(results_df, args.threads, args.advanced)

    # Sort by Total (sort = 1), Recent ( = 2), Prev ( = 3), Change ( = 4), Rockets ( = 5)
    results_df.sort_values(by=results_df.columns[args.sort - 1], inplace=True, ascending=False)

    print_df(results_df, 'output\' + args.filename, args.csv)
    total_time = str(timedelta(seconds=round(time.time() - start)))
    print("AutoDD took " + total_time + " (H:MM:SS).")
    print("Dataframe has {} rows".format(len(results_df.index)))

if __name__ == '__main__':
    main()
