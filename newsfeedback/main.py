import trafilatura, click, re, time
import pandas as pd
from trafilatura import feeds
from loguru import logger as log
from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException

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

### Best case functions

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
    sequence of actions. The results are stored in a dataframe.
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

### Worst case functions 

def get_article_urls_worst_case(homepage_url):
    """ Retrieves URLs from a given homepage through beautiful soup, by getting all href attributes of
    an a tag. Prints out the number of articles found if at least one has been retrieved. 
    """
    article_list = feeds.find_feed_urls(homepage_url)
    article_url_list = []
    downloaded = trafilatura.fetch_url(homepage_url)
    soup = BeautifulSoup(downloaded, 'html.parser')
    for a in soup.find_all('a'):
        href = a.get('href')
        http_check = re.search(r'(http)', f'{href}')
        if href != None:
            if http_check == None:
                http_url = f"{homepage_url}" + f"{href}"
                double_slash_check = re.search(r"(?<!https:)(//)", http_url)
                if double_slash_check:
                    http_url = re.sub(r"(?<!https:)(//)", r"/", http_url)
                double_de_check = re.search(r"/de/de/", http_url)
                if double_de_check:
                    http_url = re.sub(r"/de/de/", r"/de/", http_url)
                article_url_list.append(http_url)
            else:
                homepage_de = re.search(r'(https://www\..+?\.\w{2,3}/de/)', homepage_url)
                if homepage_de:
                    homepage_split = homepage_de.group(0)
                else:
                    homepage_split = re.search(r'(https://www\..+?\.\w{2,3})', homepage_url).group(0)
                homepage_check = re.search(fr'{homepage_split}/.+', href)
                if homepage_check:
                    article_url_list.append(href)
    article_url_list = list(dict.fromkeys(article_url_list)) # refactor these!
    article_url_list = list(filter(lambda item: item is not None, article_url_list))
    print(f'{len(article_url_list)} links have been found.\r')
    get_article_urls_worst_case.article_url_list = article_url_list
    return get_article_urls_worst_case.article_url_list

def get_article_metadata_worst_case(article_url, metadata_wanted):
    """ Extracts predefined (metadata_wanted) metadata from the given article url. 
    Returns an empty dict if no metadata is found.
    """
    downloaded = trafilatura.fetch_url(article_url)
    if downloaded != None:
        metadata = trafilatura.bare_extraction(downloaded, only_with_metadata=True, include_links=True)
        if metadata != None:
            dict_keys = list(metadata.keys()) # look into refactoring the following bit of code at some point
            dict_keys_to_pop = [key for key in dict_keys if key not in metadata_wanted]
            for key in dict_keys_to_pop: 
                metadata.pop(key, None)
        else:
            metadata = {}
    else:  
        metadata = {}
    #metadata = {metadata_key: metadata_value for metadata_key, metadata_value in metadata.items() if metadata_key and metadata_value}
    get_article_metadata_worst_case.metadata = metadata
    return get_article_metadata_worst_case.metadata

def get_article_urls_and_metadata_worst_case(homepage_url, metadata_wanted): # might be a bit slow
    """ Combines get_article_urls_wost_case() and get_article_metadata_worst_case() for a seamless 
    sequence of actions. The results are stored in a dataframe.
    """
    get_article_urls_worst_case(homepage_url)
    article_url_list = get_article_urls_worst_case.article_url_list
    article_list = []
    for article_url in article_url_list:
        if article_url != None:
            print(article_url)
            get_article_metadata_worst_case(article_url, metadata_wanted)
            metadata =  get_article_metadata_worst_case.metadata
            if len(metadata) != 0: # nested a bit too deep for my tastes, will refactor eventually
                article_list.append(metadata)
    print(f'{homepage_url}: {len(article_list)} articles have been found.\r')
    df = pd.DataFrame.from_dict(article_list)
    print(df)
    get_article_urls_and_metadata_worst_case.df = df
    return get_article_urls_and_metadata_worst_case.df

### Filter-related functions

def filter_urls(article_url_list):
    """ Filters out non-viable article URLs through a whitelist.
    Criteria: url ends in word character (-> not a / )"""
    article_url_list_clean = []
    for article in article_url_list:
        viable_article = re.search(r"((/(\w+-)+\w+-\w+(\.html)?)|/-/\w+)", article)
        if viable_article:
            article_url_list_clean.append(article)
    print(f'Removed {(len(article_url_list)-len(article_url_list_clean))} superfluous URLs.')
    filter_urls.article_url_list_clean = article_url_list_clean
    return filter_urls.article_url_list_clean

def get_filtered_article_urls_and_metadata_best_case(homepage_url, metadata_wanted):
    """ Combines get_article_urls_best_case(), filter_urls() and get_article_metadata_best_case()
    for a seamless sequence of actions. The results are stored in a dataframe.
    """
    get_article_urls_best_case(homepage_url)
    article_url_list = get_article_urls_best_case.article_url_list
    article_url_list_clean = filter_urls(article_url_list)
    article_list = []
    if len(article_url_list_clean) != 0:
        for article_url in article_url_list_clean:
            get_article_metadata_best_case(article_url, metadata_wanted)
            metadata =  get_article_metadata_best_case.metadata
            article_list.append(metadata)
    df = pd.DataFrame.from_dict(article_list)
    get_article_urls_and_metadata_best_case.df = df
    return get_article_urls_and_metadata_best_case.df
    
def get_filtered_article_urls_and_metadata_worst_case(homepage_url, metadata_wanted):
    """ Combines get_article_urls_wost_case(), filter_urls() and get_article_metadata_worst_case() 
    for a seamless sequence of actions. The results are stored in a dataframe.
    """
    get_article_urls_worst_case(homepage_url)
    article_url_list = get_article_urls_worst_case.article_url_list
    article_url_list_clean = filter_urls(article_url_list)
    article_list = []
    for article_url in article_url_list_clean:
        if article_url != None:
            get_article_metadata_worst_case(article_url, metadata_wanted)
            metadata =  get_article_metadata_worst_case.metadata
            if len(metadata) != 0: # nested a bit too deep for my tastes, will refactor eventually
                article_list.append(metadata)
    print(f'{homepage_url}: {len(article_list)} articles have been found.\r')
    df = pd.DataFrame.from_dict(article_list)
    print(df)
    get_article_urls_and_metadata_worst_case.df = df
    return get_article_urls_and_metadata_worst_case.df

### Site specific functions

def accept_pur_abo(homepage_url, class_name):
    """ Finds the iFrame and the consent button and clicks on it, 
    waiting on the ZEIT homepage to load. Currently not compatible with GeckoDriver.
    """
    options = webdriver.ChromeOptions()
    options.add_argument('headless') # comment out if you want to see what's happening
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    driver.get(homepage_url)
    try:
        WebDriverWait(driver, 10).until(EC.frame_to_be_available_and_switch_to_it(0))
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, class_name))).click()
        driver.switch_to.default_content()
        WebDriverWait(driver, 10).until(EC.title_is('ZEIT ONLINE | Nachrichten, News, Hintergründe und Debatten'))
        text = driver.page_source
    except TimeoutException:
        text = 'Element could not be found, connection timed out.'
    finally:
        print(text.encode('utf-8'))
        driver.quit()
    return  text

### Export

def export_dataframe(df, homepage_url, output_folder):
    """ Exports a given dataframe, naming it based on datetime and homepage url.
    """
    df_name = re.search(r"\..+?\.",f"{homepage_url}").group(0)
    df_name = df_name.replace(".","") 
    timestr = time.strftime(r"%Y%m%d-%H%M")
    df_path = f"{output_folder}/{timestr}-"+f"{df_name}"+f".csv"
    df.to_csv(df_path, index=False, mode='a')
    export_dataframe.df_path = df_path
    return export_dataframe.df_path

if __name__ == "main":
    cli()