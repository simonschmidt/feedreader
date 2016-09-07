import gevent.monkey
gevent.monkey.patch_all(thread=False)

import gevent
from gevent import queue
import queue as builtin_queue

import click
import feedparser
import requests
from cachecontrol import CacheControl
from furl import furl
import dateutil.parser

import uuid
import hashlib
import random
import time
import sys
import textwrap
import logging

log = logging.getLogger(__name__)

orig_session = requests.session()
orig_session.headers = {'User-Agent': 'feedreader github.com/simonschmidt/feedreader'}

session = CacheControl(orig_session)


class Feed(object):
    """
    A self-refreshing feed.

    Arguments:
        url(str): Feed url
        interval(int): Polling interval
        include_initial(bool): Include items from first update

    Attributes:
        subscribers(set): Queues that will recieve content on updates


    Example:
        >>> feed = Feed('example://foo')
        >>> q = queue.Queue()
        >>> feed.subscribers.add(q)
    """
    RETRY_DELAY = 60

    def __init__(self, url, interval=60, include_initial=False, _spawn_greenlet=True):
        self.url = url
        self.interval = interval
        self._discard_next_update = not include_initial

        # Queues for interested parties
        self.subscribers = set()

        # All seen id's, worth limiting size of this?
        self._old_ids = set()

        # Start fetching
        if _spawn_greenlet:
            self._greenlet = gevent.spawn(self._fetcher)

    def update(self):
        """Manually trigger update"""
        items = self._get_new_items()

        if self._discard_next_update:
            self._discard_next_update = False
            items = []

        self._notify_subscribers(items)

        return items

    def _notify_subscribers(self, items):
        for item in items:
            for q in self.subscribers:
                try:
                    q.put_nowait((self, item))
                except Exception:
                    log.exception("Failed to enqueue item")

    def _get_new_items(self):
        items = _items_from_feed(self.url, skip_ids=self._old_ids)

        for item in items:
            self._old_ids.add(_item_id(item))

        return items

    def _fetcher(self):
        """Schedule updates"""
        while True:
            if len(self.subscribers) == 0:
                log.debug("Nobody cares about %s", self)
                gevent.sleep(1)
                continue

            try:
                log.debug("Updating feed %s", self)
                self.update()
                log.debug("Updated feed %s", self)
            except Exception as exc:
                retry_delay = min(self.RETRY_DELAY, self.interval)
                log.warning("Unable to update %s, retrying in %s seconds", self, retry_delay, exc_info=True)
                gevent.sleep(retry_delay)
                continue

            # BUG: If interval is lowered it wont take effect until after next update
            gevent.sleep(self.interval)

    def __repr__(self):
        return "Feed<url='{}', interval={}>".format(self.url, self.interval)


def _item_id(item):
    """ID for a feed item"""
    if item.id:
        return item.id

    # No ID, concat title and published *shrug*
    return hashlib.sha256("{}|{}".format(item.title, item.published)).hexdigest()


def _items_from_feed(url, skip_ids=None):
    scheme = furl(url).scheme

    if scheme == 'example':
        items = _fake_items(url)
    elif scheme in ('http', 'https'):
        r = session.get(url)
        r.raise_for_status()
        items = feedparser.parse(r.text).entries
    else:
        # It's a baby whale Jay!
        raise ValueError("Unsupported scheme '{}' in '{}'".format(scheme, url))

    items = [
        item
        for item in items
        if (skip_ids is None) or (_item_id(item) not in skip_ids)]
    items.sort(key=lambda x: x.published_parsed or x.id)

    return items


class FakeEntry(object):
    def __init__(self, id_=None):
        self.id = id_ or str(uuid.uuid4())
        self.title = "<example>"
        self.link = "example://{}".format(self.id)
        self.published = '2001-02-03 04:05:06'
        self.published_parsed = None


def _fake_items(url):
    if url != 'example://test':
        time.sleep(random.randint(1, 2))
        if random.random() < 0.3:
            raise RuntimeError("eth0 on fire")

    return [FakeEntry('old_id'), FakeEntry()]


def test_initial_items_excluded():
    f = Feed("example://test", _spawn_greenlet=False)

    assert len(f.update()) == 0
    assert len(f.update()) > 0


def test_item_included_exactly_once():
    f = Feed('example://test', include_initial=True, _spawn_greenlet=False)

    initial_ids = [_item_id(item) for item in f.update()]
    assert 'old_id' in initial_ids

    new_ids = [_item_id(item) for item in f.update()]
    assert len(new_ids) > 0
    assert 'old_id' not in new_ids


def test_items_are_queued():
    q = builtin_queue.Queue()
    f = Feed('example://test', include_initial=True, _spawn_greenlet=False)

    f.subscribers.add(q)
    f.update()

    (f_res, item) = q.get()
    assert f_res is f


@click.command()
@click.option(
    '--loglevel',
    type=click.Choice(['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']),
    default='ERROR')
@click.option('--interval', default=5 * 60, metavar='SECONDS', help='Update interval')
@click.option('--include-initial/--drop-initial', default=False)
@click.argument('urls', nargs=-1, metavar='URL...')
def main(*, interval, loglevel, include_initial, urls):
    """Feed reader for RSS and Atom"""
    logging.basicConfig(level=loglevel, stream=sys.stderr)

    print_queue = queue.Queue()
    for url in urls:
        feed = Feed(url, interval, include_initial=include_initial)
        feed.subscribers.add(print_queue)

    def printer():
        template = '\n'.join(("{date}", "{feed}", "  {title}", "  {link}", ""))
        for feed, item in print_queue:
            title_lines = '\n  '.join(textwrap.wrap(item.title))
            output = template.format(
                date=dateutil.parser.parse(item.published),
                feed=feed,
                title=title_lines,
                link=item.link)
            print(output)

    printer_greenlet = gevent.spawn(printer)
    gevent.wait([printer_greenlet])
