from os.path import isfile
from proxy_checker import ProxyChecker
from concurrent.futures import ThreadPoolExecutor

class Proxies:
    def __init__(self, proxy_filename=None):
        self.proxy_list = self.get_proxies(proxy_filename)

    @staticmethod
    def get_proxies(proxy_filename):
        if proxy_filename:
            if not isfile(proxy_filename):
                raise ValueError("Invalid filename: {}".format(proxy_filename))
            proxies = []
            with open(proxy_filename) as file:
                for line in file:
                    # remove comments and whitespace
                    line = line.split("#")[0].strip()
                    if line:
                        # if line contains "passhtrough", retrieve data without proxy as one thread
                        if line == "passthrough":
                            proxies.append("")
                        else:
                            proxies.append(line)
        else:
            # ie no proxy
            proxies = [""]

        return proxies

    @staticmethod
    def check_proxy(proxy_str):
        proxy_split = proxy_str.split('@')
        first_part = proxy_split[0]
        proxy = proxy_split[1]

        first_part_split = first_part.split('//')
        user_password = first_part_split[1]
        user_password_split = user_password.split(':')
        user = user_password_split[0]
        password = user_password_split[1]

        checker = ProxyChecker()
        check_dict = checker.check_proxy(proxy=proxy, user=user, password=password)
        return check_dict

    def check_proxies(self):
        # get rid of empty string in list if there
        proxy_list = [proxy for proxy in self.proxy_list if proxy]

        executor = ThreadPoolExecutor(max_workers=len(proxy_list))

        results = list(executor.map(self.check_proxy, proxy_list))

        print('-' * 125)
        for idx, proxy_str in enumerate(proxy_list):
            proxy = proxy_str.split('@')[1]
            print("proxy: {}".format(proxy))
            print(results[idx])
            print('-' * 125)