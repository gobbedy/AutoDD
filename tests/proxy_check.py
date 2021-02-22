from proxy_checker import ProxyChecker
from src import utils
from concurrent.futures import ThreadPoolExecutor

def check_proxy(proxy_str):
    proxy_split = proxy_str.split('@')
    first_part = proxy_split[0]
    proxy = proxy_split[1]

    first_part_split = first_part.split('//')
    user_password = first_part_split[1]
    user_password_split = user_password.split(':')
    user = user_password_split[0]
    password = user_password_split[1]

    check_dict = checker.check_proxy(proxy=proxy, user=user, password=password)
    return check_dict

filename = "../input/proxies.txt"
proxy_list = utils.get_proxies(filename)

# get rid of empty string in list if there
proxy_list = [proxy for proxy in proxy_list if proxy]
checker = ProxyChecker()
executor = ThreadPoolExecutor(max_workers=len(proxy_list))

results = list(executor.map(check_proxy, proxy_list))

print('-'*125)
for idx, proxy_str in enumerate(proxy_list):
    proxy = proxy_str.split('@')[1]
    print("proxy: {}".format(proxy))
    print(results[idx])
    print('-'*125)