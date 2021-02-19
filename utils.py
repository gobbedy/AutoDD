import copy
from datetime import datetime, timedelta

def gen_slices(num_splits, payload, search_window=365):
    """Creates a list of payloads"""

    if 'after' not in payload:
        search_window = timedelta(days=search_window)
        before = payload['before']
        after = int((datetime.fromtimestamp(before) - search_window).timestamp())

    else:
        before = payload['before']
        after = payload['after']

    # create time slices
    ts = timeslice(after, before, num_splits)
    slices = [mapslice(copy.deepcopy(payload), ts[i+1], ts[i]) for i in range(num_splits)]

    return slices


def timeslice(after, before, num):
    return [int((before - after) * i / num + after) for i in reversed(range(num + 1))]


def mapslice(payload, after, before):
    payload['before'] = before
    payload['after'] = after
    return payload