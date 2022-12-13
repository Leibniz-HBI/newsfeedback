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
    """ Retrieves article URLs from a given homepage trafilatura's find_feed_urls function.
    Prints out the number of articles found if at least one has been retrieved.
    """
    article_url_list = feeds.find_feed_urls(homepage_url)
    if len(article_url_list) != 0:
        print(f'{len(article_url_list)} articles have been found.\r')
    get_article_urls_best_case.article_url_list = article_url_list
    return get_article_urls_best_case.article_url_list

def get_article_metadata_best_case(article_url, metadata_wanted):
    """ Extracts predefined (metadata_wanted) metadata from the given article url. Returns an empty list if
    no metadata is found.
    """
    downloaded = trafilatura.fetch_url(article_url)
    metadata = trafilatura.bare_extraction(downloaded, only_with_metadata=True, include_links=True)
    if metadata is not None:
        dict_keys = list(metadata.keys())
        dict_keys_to_pop = [key for key in dict_keys if key not in metadata_wanted]
        for key in dict_keys_to_pop: 
            metadata.pop(key, None)
    else:
        metadata = []
    get_article_metadata_best_case.metadata = metadata
    return get_article_metadata_best_case.metadata
    
def get_article_urls_and_metadata_best_case(homepage_url, metadata_wanted):
    """ Combines get_article_urls_best_case() and get_article_metadata_best_case() for a seamless 
    seqence of actions. The results are stored in a dataframe.
    """
    get_article_urls_best_case(homepage_url)
    article_url_list = get_article_urls_best_case.article_url_list
    article_list = []
    for article_url in article_url_list:
        get_article_metadata_best_case(article_url, metadata_wanted)
        metadata =  get_article_metadata_best_case.metadata
        article_list.append(metadata)
    df = pd.DataFrame.from_dict(article_list)
    get_article_urls_and_metadata_best_case.df = df
    return get_article_urls_and_metadata_best_case.df
        
if __name__ == "main":
    cli()
