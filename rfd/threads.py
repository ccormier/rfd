import re
import json
import time
from colorama import Fore, Style
from . import API_BASE_URL
from .scores import calculate_score, get_vote_color


class Thread:
    def __init__(self, title, dealer_name, score, url, views, topic_id, post_time):
        self.dealer_name = dealer_name
        self.score = score
        self.title = title
        self.url = url
        self.views = views
        self.topic_id = topic_id
        self.post_time = post_time

    def __repr__(self):
        return f"Thread({self.title})"


class ThreadEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Thread):
            return dict(
                dealer_name=o.dealer_name,
                score=o.score,
                title=o.title,
                url=o.url,
                views=o.views,
                topic_id=o.topic_id,
                post_time=o.post_time,
            )
        return json.JSONEncoder.default(self, o)


def build_web_path(slug):
    return f"{API_BASE_URL}{slug}"


def get_dealer(topic):
    dealer = None
    if topic.get("offer"):
        dealer = topic.get("offer").get("dealer_name")
    return dealer


def parse_threads(threads):
    """Parse topics list api response into digestible list.

    Arguments:
        threads {dict} -- topics response from rfd api

    Returns:
        list(dict) -- digestible list of threads
    """
    parsed_threads = []
    if threads is None:
        return []
    for topic in threads:
        parsed_threads.append(
            Thread(
                title=topic.get("title"),
                dealer_name=get_dealer(topic),
                score=calculate_score(topic),
                url=build_web_path(topic.get("web_path")),
                views=topic.get("total_views"),
                topic_id=topic.get("topic_id"),
                post_time=topic.get("post_time"),
            )
        )
    return parsed_threads


def sort_threads(threads, sort_by):
    """Sort threads by an attribute"""
    if sort_by is None:
        return threads
    assert sort_by in ["views", "score", "title", "topic_id", "post_time"]
    if sort_by in ["topic_id", "post_time"]:
        threads = sorted(threads, key=lambda x: getattr(x, sort_by))
    else:
        threads = sorted(threads, key=lambda x: getattr(x, sort_by), reverse=True)
    return threads


def search_threads(threads, regex):
    """Match deal title and dealer names with regex specified."""

    regexp = re.compile(str(regex).lower())

    for deal in threads:

        if regexp.search(deal.title.lower()) or (
            deal.dealer_name and regexp.search(deal.dealer_name.lower())
        ):
            yield deal

def get_newest_topic_id(threads):
    topic_id = 0
    for thread in threads:
        if int(thread.topic_id) > topic_id:
            topic_id = int(thread.topic_id)
    return topic_id

def generate_thread_output(threads):
    for count, thread in enumerate(threads, 1):
        output = ""
        dealer = thread.dealer_name
        if dealer and dealer is not None:
            dealer = "[" + dealer + "] "
        else:
            dealer = ""
        output += (
            " "
            + str(count)
            + "."
            + get_vote_color(thread.score)
            + Fore.RESET
            + f"{dealer}{thread.title}"
            + Fore.LIGHTYELLOW_EX
            + f" ({thread.views} views)"
            + Fore.RESET
        )
        output += Fore.BLUE + f" {thread.url}"
        output += Style.RESET_ALL
        output += "\n\n"
        yield output

def generate_thread_output_modified(threads, topic_tracker=None):
    for count, thread in enumerate(threads, 1):
        if topic_tracker:
            if int(thread.topic_id) > topic_tracker:
                title = Fore.RED + f'{thread.title}\a'
            else:
                title = f'{thread.title}'
        else:
            title = f'{thread.title}'
        output = ""
        dealer = thread.dealer_name
        if dealer and dealer is not None:
            dealer = "[" + dealer + "] "
        else:
            dealer = ""
        output += (
            ""
            #" "
            #+ str(count)
            #+ "."
            + "{:11s}".format(get_vote_color(thread.score))
            + Fore.RESET
            #+ f"{thread.topic_id}"
            + f"{dealer}{title}"
            + Fore.LIGHTYELLOW_EX
            + f" ({thread.views} views)"
            + Fore.RESET
        )
        output += Fore.BLUE + "\n{:7s}{}".format("", thread.url)
        output += Style.RESET_ALL
        #output += "\n\n"
        yield output

def generate_new_thread_output(threads, topic_tracker=None):
    for count, thread in enumerate(threads, 1):
        if topic_tracker >= thread.topic_id:
            #print(f'skipping {thread.topic_id}')
            continue
        if topic_tracker > 0:
            title = f'{thread.title}\a'
        else:
            title = f'{thread.title}'
        output = ""
        dealer = thread.dealer_name
        if dealer and dealer is not None:
            dealer = "[" + dealer + "] "
        else:
            dealer = ""
        output += (
            ""
            #" "
            #+ str(count)
            #+ "."
            + "{:12s}".format(get_vote_color(thread.score))
            + Fore.LIGHTYELLOW_EX
            + f" ({thread.post_time}) "
            #+ f"{thread.topic_id}"
            + Fore.RESET
            + Fore.MAGENTA + f"{dealer}" + Fore.RESET
            + f"{title}"
            + Fore.LIGHTYELLOW_EX
            + f" ({thread.views} views)"
            + Fore.RESET
        )
        output += Fore.BLUE + "\n{:9s}{}".format("", thread.url)
        output += Style.RESET_ALL
        #output += "\n\n"
        yield output, thread
