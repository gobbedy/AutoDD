import requests
import pandas as pd
from numbers import Number
from concurrent.futures import ThreadPoolExecutor
from itertools import repeat
from os import cpu_count


class FastYahoo:

    def __init__(self, threads=True):
        if threads:
            self.executor = ThreadPoolExecutor(max_workers=cpu_count()*2)
            self._map = self.executor.map
        else:
            self._map = map

    def download_advanced_stats(self, symbol_list, module_name_map):
        """
        Downloads advanced yahoo stats for many tickers by doing one request per ticker.
        """
        # get raw responses
        results = self._map(FastYahoo.get_ticker_stats, symbol_list, repeat(module_name_map))

        # construct stats table from responses
        stats_table = []
        for idx, retrieved_modules_dict in enumerate(results):
            stats_list = [symbol_list[idx]]
            for module_name, stat_name_dict in module_name_map.items():
                retrieved_stats_dict = None
                if retrieved_modules_dict is not None and module_name in retrieved_modules_dict:
                    retrieved_stats_dict = retrieved_modules_dict[module_name]
                stats_list.extend(FastYahoo.retrieve_stats(retrieved_stats_dict, stat_name_dict))
            stats_table.append(stats_list)

        columns = ['Symbol']
        for stat_name_dict in module_name_map.values():
            columns.extend(list(stat_name_dict.values()))

        financial_data_df = pd.DataFrame(stats_table, columns=columns)
        financial_data_df.set_index('Symbol', inplace=True)

        return financial_data_df

    def download_quick_stats(self, symbol_list, quick_stats_dict):
        """
        Downloads select ("quick") stats for many tickers using minimal number of http requests. Splits the ticker list
        into groups of 1000 and performs one request per group. eg if list has 2350 tickers, will split into 2 groups of
        1000 tickers and one group with the remaining 350 tickers, and will get quick stats with only 3 http requests.
        Only returns those tickers that are valid, thus can be used to validate tickers efficiently.
        """
        # through trial and error, 1179 was the max without returning an error, but that number feels too arbitrary
        max_params = 1000

        # split symbol_list into chunks of size max_params
        request_symbol_lists = [symbol_list[i:i + max_params] for i in range(0, len(symbol_list), max_params)]

        # get raw responses
        results = self._map(FastYahoo.quick_stats_request, request_symbol_lists, repeat(list(quick_stats_dict.keys())))

        # construct stats table from responses
        stats_table = []
        for response_list in results:
            # each iteration is one symbol; (eg SIGL, AAPL)
            for retrieved_stats_dict in response_list:
                symbol = retrieved_stats_dict['symbol']
                stats_list = [symbol] + FastYahoo.retrieve_stats(retrieved_stats_dict, quick_stats_dict)
                stats_table.append(stats_list)

        # construct dataframe
        columns = ['Symbol'] + list(quick_stats_dict.values())
        stats_df = pd.DataFrame(stats_table, columns=columns)
        stats_df.set_index('Symbol', inplace=True)

        return stats_df

    @staticmethod
    def retrieve_stats(retrieved_stats_dict, stat_name_dict):
        stats_list = []
        if retrieved_stats_dict is not None:
            for stat_name in stat_name_dict.keys():
                stat_val = 'N/A'
                if stat_name in retrieved_stats_dict:
                    stat = retrieved_stats_dict[stat_name]
                    if isinstance(stat, dict):
                        if stat:  # only if non-empty otherwise N/A
                            stat_val = stat['raw']
                    elif isinstance(stat, str) or isinstance(stat, Number):
                        stat_val = stat
                    else:
                        raise TypeError('Expected dictionary, string or number.')
                stats_list.append(stat_val)
        else:
            stats_list.extend(['N/A'] * len(stat_name_dict.keys()))
        return stats_list

    @staticmethod
    def get_ticker_stats(symbol, module_name_map):
        """
        Returns advanced stats for one ticker
        """

        url = 'https://query2.finance.yahoo.com/v10/finance/quoteSummary/' + symbol
        module_list = list(module_name_map.keys())
        params = {
            'modules': ','.join(module_list),
        }
        result = requests.get(url, params=params)
        if result.status_code != 200 and result.status_code != 404:
            result.raise_for_status()

        json_dict = result.json()
        if "quoteSummary" not in json_dict:
            return None
        if json_dict['quoteSummary']['result'] is None:
            return None
        module_dict = json_dict['quoteSummary']['result'][0]

        return module_dict

    @staticmethod
    def quick_stats_request(request_symbol_list, field_list):
        """
        Returns quick stats for up to 1000 tickers in one request. Only returns those tickers that are valid, thus can
        be used to validate tickers efficiently.
        """
        params = {
            'formatted': 'True',
            'symbols': ','.join(request_symbol_list),
            'fields': ','.join(field_list),
        }
        result = requests.get("https://query1.finance.yahoo.com/v7/finance/quote", params=params)
        if result.status_code != 200 and result.status_code != 404:
            result.raise_for_status()

        json_dict = result.json()
        if "quoteResponse" not in json_dict:
            return None
        data_list = json_dict['quoteResponse']['result']

        return data_list


# https://query2.finance.yahoo.com/v10/finance/quoteSummary/aapl?modules=summaryDetail -- for payoutRatio
# https://query2.finance.yahoo.com/v10/finance/quoteSummary/nakd?modules=summaryProfile -- for industry
# https://query2.finance.yahoo.com/v10/finance/quoteSummary/aapl?modules=financialData -- quickRatio
# https://query2.finance.yahoo.com/v10/finance/quoteSummary/nakd?modules=price -- regularMarketChangePercent (available in quotes but not other modules)
# https://query2.finance.yahoo.com/v10/finance/quoteSummary/nakd?modules=defaultKeyStatistics -- floatShares (available in quotes but not other modules)

# https://query2.finance.yahoo.com/v10/finance/quoteSummary/aapl?modules=summaryDetail,summaryProfile,financialData,price,defaultKeyStatistics -- basically all data
