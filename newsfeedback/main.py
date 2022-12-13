import click
import pandas as pd
import trafilatura, re
from trafilatura import feeds
from loguru import logger as log


@click.command()
@click.argument("name", type=str)
def cli(name: str) -> None:
    """ This internal function is called by the click-decorated function.
    The split into two functions is necessary for documentation purposes as pdoc3
    cannot process click-decorated functions.

    Parameters :
        name : str : name argument passed by click
    Returns:
        None: Nada   
    """
    log.info(cli_implementation(name))

def cli_implementation(name: str) -> None:
    """ Greet someone or something by name.

    Parameters:
        name : str : Whom to greet

    Return:
        str : Greeting
    """
    return f"Hello {name}!"

def get_article_urls_best_case(homepage_url):
    article_url_list = feeds.find_feed_urls(homepage_url)
    if len(article_url_list) != 0:
        print(f'{len(article_url_list)} articles have been found.\r')
    get_article_urls_best_case.article_url_list = article_url_list
    return get_article_urls_best_case.article_url_list

if __name__ == "main":
    cli()
