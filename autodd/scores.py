import re
import pandas as pd
from datetime import datetime
from tabulate import tabulate
from locale import getpreferredencoding

def get_ticker_scores(subreddit_results_dict, pattern_list):
    """
    Returns a dataframe:
    --one column per requested pattern -- ie number of instances of the pattern for each ticker
    --one column per subreddit; each column contains the score for each ticker in that subreddit

    :param subreddit_results_dict: A dictionary of results for each subreddit, as outputted by get_submissions
    :param pattern_list: a list of patterns to search for
    """

    # Python regex pattern for stocks codes
    ticker_pattern = r'(?<=\$)?\b[A-Z]{3,5}\b(?:\.[A-Z]{1,2})?'

    # Dictionaries containing the summaries
    subreddit_scores_dict = {subreddit: {} for subreddit in subreddit_results_dict.keys()}

    # Dictionaries containing the pattern count
    pattern_scores_dict = {pattern: {} for pattern in pattern_list}

    for subreddit, submission_list in subreddit_results_dict.items():
        # looping over each submission
        for submission_dict in submission_list:
            score = submission_dict.get('score', 1) - 1

            # search the title for the ticker/tickers
            title = submission_dict.get('title', '')
            title_tickers = set(re.findall(ticker_pattern, title))

            # search the text body for the ticker/tickers
            selftext = submission_dict.get('selftext', '')
            selftext_tickers = set(re.findall(ticker_pattern, selftext))

            extracted_tickers = selftext_tickers.union(title_tickers)
            # brk.b recognized by yahoo as brk-b; on the other hand aab.to is recognized as aab.to
            # so add both '.' and '_' versions and will let yahoo remove the invalid ones
            extracted_tickers = {x for ticker in extracted_tickers for x in (ticker.replace('.', '_'), ticker)}

            for ticker in extracted_tickers:
                for pattern in pattern_scores_dict:
                    count_pattern = title.count(pattern) + selftext.count(pattern)
                    pattern_scores_dict[pattern][ticker] = pattern_scores_dict[pattern].get(ticker, 0) + count_pattern

            for ticker in extracted_tickers:
                subreddit_scores_dict[subreddit][ticker] = subreddit_scores_dict[subreddit].get(ticker, 0) + score

    scores_df = pd.DataFrame.from_dict(subreddit_scores_dict).fillna(value=0).astype('int32')
    scores_df.index.name = 'Ticker'
    pattern_df = pd.DataFrame.from_dict(pattern_scores_dict).fillna(value=0).astype('int32')
    return scores_df, pattern_df

def gen_delta_df(current_scores_df, prev_scores_df, interval):
    """
    Combine two score dataframes, one from the current time interval, and one from the past time interval
    :returns: dataframe containing total score, score of current interval, score of prev interval, and delta
    """
    recent = current_scores_df.sum(axis=1)
    prev = prev_scores_df.sum(axis=1)
    total = recent.add(prev, fill_value=0)
    change = recent.subtract(prev, fill_value=0)

    first_col = str(interval) + 'H Total'
    columns = [first_col, 'Prev', 'Recent', 'Change']
    df = pd.concat([total, prev, recent, change], axis=1).fillna(value=0).astype('int32')
    df.columns = columns

    return df


def filter_df(df, min_val):
    """
    Filter the score dataframe

    :param dataframe df: the dataframe to be filtered
    :param int min_val: the minimum total score
    :returns: the filtered dataframe
    """
    banned_words = [
        'THE', 'FUCK', 'ING', 'CEO', 'USD', 'WSB', 'FDA', 'NEWS', 'FOR', 'YOU', 'AMTES', 'WILL', 'CDT', 'SUPPO',
        'MERGE', 'BUY', 'HIGH', 'ADS', 'FOMO', 'THIS', 'OTC', 'ELI', 'IMO', 'TLDR', 'SHIT', 'ETF', 'BOOM', 'THANK',
        'PPP', 'REIT', 'HOT', 'MAYBE', 'AKA', 'CBS', 'SEC', 'NOW', 'OVER', 'ROPE', 'MOON', 'SSR', 'HOLD', 'SELL',
        'COVID', 'GROUP', 'MONDA', 'USA', 'YOLO', 'MUSK', 'AND', 'STONK', 'ELON', 'CAD', 'WIN', 'GET', 'BETS',
        'INTO',
        'JUST', 'MAKE', 'NEED', 'BIG', 'STONK', 'ELON', 'CAD', 'OUT', 'TOP', 'ALL', 'ATH', 'ANY', 'AIM', 'IPO',
        'EDIT'
    ]

    # compares the first column, which is the total score to the min val
    df = df[df.iloc[:, 0] >= min_val]
    drop_index = pd.Index(banned_words).intersection(df.index)
    df = df.drop(index=drop_index)

    return df


def print_df(df, filename, writecsv):

    # turn index (symbols) into regular column for printing purposes
    df.reset_index(inplace=True)

    now = datetime.now()
    # dd/mm/YY H:M:S
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")

    if writecsv:
        filename += '.csv'
        df.to_csv(filename, index=False, float_format='%.3f', mode='a', encoding=getpreferredencoding())
        print(file=open(filename, "a"))
    else:
        filename += '.txt'
        with open(filename, "a") as file:
            file.write("date and time now = ")
            file.write(dt_string)
            file.write('\n')
            file.write(tabulate(df, headers='keys', floatfmt='.3f', showindex=False))
            file.write('\n\n')

    print("Wrote to file successfully: ")
    print(filename)

