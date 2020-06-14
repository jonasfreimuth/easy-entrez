from functools import wraps
from math import ceil
from time import sleep
from typing import Iterable
from warnings import warn


try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable):
        return iterable


def batches(data, batch_size=100):
    return [
        data[i * batch_size:(i + 1) * batch_size]
        for i in range(0, ceil(len(data) / batch_size))
    ]


def suport_batches(func):
    """
    Call the decorated functions with the collection from the first argument
    (second if counting with self) split into batches, resuming on failures
    with a interval twice the between-batch interval.
    """

    @wraps(func)
    def batches_support_wrapper(self: 'EntrezAPI', collection: Iterable, *args, **kwargs):
        size = self._batch_size
        interval = self._batch_sleep_interval
        if size is not None:
            assert isinstance(size, int)
            by_batch = {}

            for i, batch in enumerate(tqdm(batches(collection, size=size))):
                done = False

                while not done:
                    try:
                        batch_result = func(self, *args, **kwargs)
                        done = True
                    except Exception:
                        warn(f'Failed to fetch for {i}-th batch, retrying in {interval * 2} seconds')
                        sleep(interval * 2)

                by_batch[tuple(batch)] = batch_result
                sleep(interval)
            return by_batch
        else:
            return func(self, collection, *args, **kwargs)

    return batches_support_wrapper