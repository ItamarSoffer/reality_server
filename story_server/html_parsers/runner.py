import multiprocessing as mp
from multiprocessing.pool import ThreadPool
from .__main__ import HtmlParser


def fetch_event_extra_data(event_data, username):

    print("process is done by {}".format(mp.current_process().name))
    # check if the regex matches before starts
    extra_data_parser = HtmlParser(event_data['link'], username)
    extra_data = extra_data_parser.match_parser()
    if extra_data:
        print("MATCHED! {}".format(event_data['link']))
        event_data['extra_data'] = extra_data
    return event_data


def fetch_story_extra_data(events, username):
    """
    runs and fetchs the exta data. does is with MultiProcessing
    :param events:
    :param username:
    :return:
    """
    mp_results = []
    no_extra = []
    pool = ThreadPool(5)

    import time
    start = time.perf_counter()

    for event_data in events:
        if event_data['link']:
            mp_results.append(pool.apply_async(fetch_event_extra_data, args=(event_data, username )))
            # print('{}'.format(time.perf_counter() - start))
        else:
            no_extra.append(event_data)
    print(' all started: {}'.format(time.perf_counter() - start))

    output = [p.get() for p in mp_results]
    pool.close()

    end = time.perf_counter()
    print("all ended: {} seconds".format(end - start))

    final_results = output + no_extra
    return sorted(final_results, key=lambda d: d['event_time'], reverse=True)