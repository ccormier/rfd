from __future__ import unicode_literals


import logging
import sys
import json
import click
import time

PUSHOVER=False
if PUSHOVER:
    from .pushover import PushOver
    po = PushOver('', '')

try:
    from importlib import metadata
except ImportError:  # for Python<3.8
    import importlib_metadata as metadata
from colorama import init
from .api import get_threads, get_posts
from .threads import (
    parse_threads,
    search_threads,
    sort_threads,
    generate_thread_output,
    generate_new_thread_output,
    ThreadEncoder,
    get_newest_topic_id,
)
from .posts import generate_posts_output, PostEncoder


init()

logging.getLogger()
logging.getLogger().setLevel(logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler())

def get_version():
    return "rfd v" + metadata.version("rfd")


def print_version(ctx, _, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo(get_version(), nl=True)
    ctx.exit()


@click.group(invoke_without_command=True)
@click.option(
    "-v",
    "--version",
    is_flag=True,
    callback=print_version,
    expose_value=False,
    is_eager=True,
)
@click.pass_context
def cli(ctx):
    """CLI for https://forums.redflagdeals.com"""
    if not ctx.invoked_subcommand:
        click.echo(ctx.get_help())


@cli.command(short_help="Display all posts in a thread.")
@click.argument("post_id")
@click.option(
    "--output", default=None, help="Defaults to custom formatting. Other options: json"
)
def posts(post_id, output):
    """Iterate all pages and display all posts in a thread.

    post_id can be a full url or post id only

    Example:

    \b
    rfd posts https://forums.redflagdeals.com/koodo-targeted-public-mobile-12-120-koodo-5gb-40-no-referrals-2173603
    """

    try:
        if output == "json":
            click.echo_via_pager(
                json.dumps(
                    get_posts(post=post_id),
                    cls=PostEncoder,
                    indent=2,
                    sort_keys=True,
                )
            )
        else:
            click.echo_via_pager(generate_posts_output(get_posts(post=post_id)))

    except ValueError:
        click.echo("Invalid post id.")
        sys.exit(1)
    except AttributeError as err:
        click.echo("The RFD API did not return the expected data. %s", err)
        sys.exit(1)

@cli.command(short_help="Displays threads in the forum. Defaults to hot deals.")
@click.option("--forum-id", default=9, help="The forum id number")
@click.option("--pages", default=1, help="Number of pages to show. Defaults to 1.")
@click.option("--sort-by", default=None, help="Sort threads by")
@click.option(
    "--output", default=None, help="Defaults to custom formatting. Other options: json"
)
def threads(forum_id, pages, sort_by, output):
    """Display threads in the specified forum id. Defaults to 9 (hot deals).

    Popular forum ids:

    \b
    9 \t hot deals
    14 \t computer and electronics
    15 \t offtopic
    17 \t entertainment
    18 \t food and drink
    40 \t automotive
    53 \t home and garden
    67 \t fashion and apparel
    74 \t shopping discussion
    88 \t cell phones
    """
    _threads = sort_threads(
        parse_threads(get_threads(forum_id, pages)), sort_by=sort_by
    )
    if output == "json":

        click.echo(
            json.dumps(
                sort_threads(_threads, sort_by=sort_by),
                cls=ThreadEncoder,
                indent=2,
                sort_keys=True,
            )
        )
    else:
        #click.echo_via_pager(generate_thread_output(_threads))
        thread_list = list((generate_thread_output(_threads)))
        #for i in thread_list:
        for i in thread_list[-10:]:
            click.echo(i)

@cli.command(short_help="Displays threads in the forum. Defaults to hot deals.")
@click.option("--forum-id", default=9, help="The forum id number")
@click.option("--pages", default=1, help="Number of pages to show. Defaults to 1.")
@click.option("--sort-by", default=None, help="Sort threads by")
@click.option("--refresh", default=10, help="Time between refresh")
@click.option(
    "--output", default=None, help="Defaults to custom formatting. Other options: json"
)
def watch_threads(forum_id, pages, sort_by, output, refresh):
    """Display threads in the specified forum id. Defaults to 9 (hot deals).

    Popular forum ids:

    \b
    9 \t hot deals
    14 \t computer and electronics
    15 \t offtopic
    17 \t entertainment
    18 \t food and drink
    40 \t automotive
    53 \t home and garden
    67 \t fashion and apparel
    74 \t shopping discussion
    88 \t cell phones
    """
    topic_tracker = 0
    while True:
        _threads = sort_threads(
            parse_threads(get_threads(forum_id, pages)), sort_by=sort_by
        )
        if output == "json":

            click.echo(
                json.dumps(
                    sort_threads(_threads, sort_by=sort_by),
                    cls=ThreadEncoder,
                    indent=2,
                    sort_keys=True,
                )
            )
        else:
            thread_list = (generate_new_thread_output(_threads, topic_tracker=topic_tracker))
            #thread_list = list((generate_new_thread_output(_threads, topic_tracker=topic_tracker)))
            #click.clear()
            #for i in thread_list[-threads:]:
            for i, obj in thread_list:
                click.echo(i)
                if topic_tracker > 0:
                    dealer = obj.dealer_name
                    if dealer and dealer is not None:
                        dealer = "[" + dealer + "] "
                    else:
                        dealer = ""
                    if PUSHOVER:
                        po.send_message(f'{dealer}{obj.title}', url=obj.url)


        n_topic = get_newest_topic_id(_threads)
        if n_topic > topic_tracker:
            topic_tracker = n_topic 

        time.sleep(refresh)


@cli.command(short_help="Search deals based on a regular expression.")
@click.option("--pages", default=5, help="Number of pages to search.")
@click.option(
    "--forum-id", default=9, help="The forum id number. Defaults to 9 (hot deals)."
)
@click.option("--sort-by", default=None, help="Sort threads by")
@click.option(
    "--output", default=None, help="Defaults to custom formatting. Other options: json"
)
@click.argument("regex")
def search(pages, forum_id, sort_by, output, regex):
    """Search deals based on regex.

    Popular forum ids:

    \b
    9 \t hot deals
    14 \t computer and electronics
    15 \t offtopic
    17 \t entertainment
    18 \t food and drink
    40 \t automotive
    53 \t home and garden
    67 \t fashion and apparel
    74 \t shopping discussion
    88 \t cell phones
    """

    matched_threads = []

    _threads = parse_threads(get_threads(forum_id, pages=pages))
    for thread in search_threads(threads=_threads, regex=regex):
        matched_threads.append(thread)

    if output == "json":
        click.echo_via_pager(
            json.dumps(
                sort_threads(matched_threads, sort_by=sort_by),
                indent=2,
                sort_keys=True,
                cls=ThreadEncoder,
            )
        )
    else:
        click.echo_via_pager(
            generate_thread_output(sort_threads(matched_threads, sort_by=sort_by))
        )
