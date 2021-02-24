from autodd.Submissions import SubmissionsPsaw, SubmissionsHybrid
from autodd.utils.utils import *
from html import unescape

filename = "../input/proxies.txt"
proxy_list = get_proxies(filename)

submissions_api_psaw = SubmissionsPsaw(proxy_list=proxy_list)
submissions_api_hybrid = SubmissionsHybrid(proxy_list=proxy_list)

ts_start = int((datetime.today() - timedelta(days=32)).timestamp())
ts_end = int((datetime.today() - timedelta(days=31)).timestamp())

search_filter = ['title', 'link_flair_text', 'selftext', 'score']

psaw_results = submissions_api_psaw.get_submissions(after=ts_start, before=ts_end, search_filter=search_filter)
hybrid_results = submissions_api_hybrid.get_submissions(after=ts_start, before=ts_end, search_filter=search_filter)

for search_filter in ['title']:
    for subreddit, results in psaw_results.items():
        for idx, submission_dict in enumerate(results):
            if search_filter in submission_dict:
                psaw_results[subreddit][idx][search_filter] = unescape(submission_dict[search_filter])

    mismatches=0
    for key in psaw_results.keys():
        '''
        psaw_items = []
        hybrid_items = []
        for result in psaw_results[key]:
            if search_filter in result:
                if result[search_filter] == '[removed]' or result[search_filter] == '[deleted]' or not result[search_filter]:
                    psaw_items.append(None)
                else:
                    psaw_items.append(result[search_filter])
            else:
                psaw_items.append(None)
        for result in hybrid_results[key]:
            if search_filter in result:
                if result[search_filter] == '[removed]' or result[search_filter] == '[deleted]' or not result[search_filter]:
                    hybrid_items.append(None)
                else:
                    hybrid_items.append(result[search_filter])
            else:
                hybrid_items.append(None)
        '''
        psaw_items = [result.get(search_filter, None) for result in psaw_results[key]]
        hybrid_items = [result.get(search_filter, None) for result in hybrid_results[key]]
        if psaw_items != hybrid_items:
            mismatches += 1
            print('boo')

if mismatches:
    print("Found {} mismatches".format(mismatches))
else:
    print("All clear! No mismatches found.")