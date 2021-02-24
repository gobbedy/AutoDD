from .FastYahoo import FastYahoo
import pandas as pd


class Financials:

    def __init__(self, threads=True):
        self.fast_yahoo = FastYahoo(threads)

    def get_financial_stats(self, results_df, advanced=False):
        """
        results_df: a dataframe whose indices are tickers
        returns a dataframe whose indices are the valid tickers (as per yahoo) from results_df; with new columns
        for the requested ticker information (eg industry, price, etc)
        """

        # TODO: should be able to build the smarts so that a single dictionary necessary, and download_advanced_stats
        # function should be able to figure out which yahoo module the stat belongs to

        # dictionary of ticker summary profile information to get from yahoo
        summary_profile_measures = {'industry': 'Industry'}

        # dictionary of ticker financial information to get from yahoo
        financial_measures = {'currentPrice': 'Price', 'quickRatio': 'QckRatio', 'currentRatio': 'CrntRatio',
                              'targetMeanPrice': 'Trgtmean', 'recommendationKey': 'Recommend'}

        # dictionary of ticker summary information to get from yahoo
        summary_measures = {'previousClose': 'prvCls', 'open': 'open', 'dayLow': 'daylow', 'dayHigh': 'dayhigh',
                            'payoutRatio': 'pytRatio', 'forwardPE': 'forwardPE', 'beta': 'beta', 'bidSize': 'bidSize',
                            'askSize': 'askSize', 'volume': 'volume', 'averageVolume': '3mAvgVol',
                            'averageVolume10days': 'avgvlmn10', 'fiftyDayAverage': '50dayavg',
                            'twoHundredDayAverage': '200dayavg'}

        # dictionary of ticker key stats summary
        key_stats_measures = {'shortPercentOfFloat': 'Short/Float%'}

        # mapping of yahoo module names to dictionaries containing data we want to retrieve
        module_name_map = {'summaryProfile': summary_profile_measures, 'defaultKeyStatistics': key_stats_measures}

        if advanced:
            module_name_map.update({'summaryDetail': summary_measures, 'financialData': financial_measures})

        # check for valid symbols and get quick stats
        ticker_list = list(results_df.index.values)
        quick_stats_df = self.get_quick_stats(ticker_list)
        valid_ticker_list = list(quick_stats_df.index.values)

        # get advanced stats
        summary_stats_df = self.fast_yahoo.download_advanced_stats(valid_ticker_list, module_name_map)
        results_df_valid = results_df.loc[valid_ticker_list]
        df = pd.concat([results_df_valid, quick_stats_df, summary_stats_df], axis=1)
        df.index.name = results_df.index.name

        return df

    def get_quick_stats(self, ticker_list):

        quick_stats = {'regularMarketPreviousClose': 'prvCls', 'fiftyDayAverage': '50DayAvg',
                       'regularMarketVolume': 'Volume', 'averageDailyVolume3Month': '3MonthVolAvg',
                       'regularMarketPrice': 'price', 'regularMarketChangePercent': '1DayChange%',
                       'floatShares': 'float'}

        unprocessed_df = self.fast_yahoo.download_quick_stats(ticker_list, quick_stats)

        processed_stats_table = []
        # TODO: if looping over rows becomes slow: vectorize. (Tested with 270 symbols and practically instantaneous)
        # See https://engineering.upside.com/a-beginners-guide-to-optimizing-pandas-code-for-speed-c09ef2c6a4d6
        for index, row in unprocessed_df.iterrows():
            symbol = index
            prev_close = row['prvCls']
            avg50day = row['50DayAvg']
            volume = row['Volume']
            avg_vol = row['3MonthVolAvg']
            price = row['price']
            day_change = row['1DayChange%']
            stock_float = row['float']

            valid = False
            if price != "N/A" and price != 0:
                valid = True

            if day_change != "N/A" and day_change != 0 or (day_change == 0 and price == prev_close):
                day_change = "{:.3f}".format(day_change)
                if day_change != 0:
                    valid = True
            elif prev_close != "N/A" and prev_close != 0 and price != "N/A":
                day_change = ((float(price) - float(prev_close)) / float(prev_close)) * 100
                day_change = "{:.3f}".format(day_change)
                if day_change != 0:
                    valid = True

            change_50day = 0
            if price != "N/A" and price != 0:
                if avg50day != "N/A" and avg50day > 0:
                    change_50day = ((float(price) - float(avg50day)) / float(avg50day)) * 100
                else:
                    change_50day = 0

            if change_50day != 0:
                change_50day = "{:.3f}".format(change_50day)

            change_vol = 0
            if volume != "N/A" and avg_vol != "N/A":
                if avg_vol != 0 and volume != 0:
                    valid = True
                    change_vol = ((float(volume) - float(avg_vol)) / float(avg_vol)) * 100

            if change_vol != 0:
                change_vol = "{:.3f}".format(change_vol)

            if stock_float != "N/A":
                stock_float = stock_float
                valid = True

            # if the ticker has any valid column, append
            if valid:
                stat_list = [symbol, price, day_change, change_50day, change_vol, stock_float]
                processed_stats_table.append(stat_list)

        # construct dataframe
        columns = ['Symbol', 'Price', '1DayChange%', '50DayChange%', 'ChangeVol%', 'Float Shares']
        stats_df = pd.DataFrame(processed_stats_table, columns=columns)
        stats_df.set_index('Symbol', inplace=True)

        return stats_df
