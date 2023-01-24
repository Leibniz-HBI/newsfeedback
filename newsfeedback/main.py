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

@click.group()
def cli():
    pass

### Best case functions

def get_article_urls_best_case(homepage_url):
    """ Retrieves article URLs from a given homepage trafilatura's find_feed_urls function.
    Prints out the number of articles found if at least one has been retrieved. 
    """
    article_url_list = feeds.find_feed_urls(homepage_url)
    if len(article_url_list) != 0:
        log.info(f'{homepage_url}: {len(article_url_list)} articles have been found.\r')
    get_article_urls_best_case.article_url_list = article_url_list
    return get_article_urls_best_case.article_url_list

def get_article_metadata_best_case(article_url, metadata_wanted):
    """ Extracts predefined (metadata_wanted) metadata from the given article url. Returns an empty list if
    no metadata is found. Only prints message if no metadata could be found.
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
        log.info(f'No metadata could be found.')
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
    log.info(f'{homepage_url}: {df.shape[0]} articles with metadata have been found.')
    return get_article_urls_and_metadata_best_case.df

### Worst case functions 

def get_article_urls_worst_case(homepage):
    """ Retrieves URLs from a given homepage through beautiful soup, by getting all href attributes of
    an a tag. Prints out the number of articles found if at least one has been retrieved. 
    """
    article_url_list = []
    if len(homepage) < 80:
        downloaded = trafilatura.fetch_url(homepage)
        homepage_url = homepage
    else:
        downloaded = homepage
        homepage_url = "https://www.zeit.de/" # un-hardcode this
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
    log.info(f'{homepage_url}: {len(article_url_list)} links have been found.\r')
    get_article_urls_worst_case.article_url_list = article_url_list
    return get_article_urls_worst_case.article_url_list

def get_article_metadata_worst_case(article, metadata_wanted):
    """ Extracts predefined (metadata_wanted) metadata from the given article url. 
    Returns an empty dict if no metadata is found.
    """
    if len(article) < 300:
        downloaded = trafilatura.fetch_url(article)
    else:
        downloaded = article
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
        log.info(f'No metadata could be found.')
    #metadata = {metadata_key: metadata_value for metadata_key, metadata_value in metadata.items() if metadata_key and metadata_value}
    get_article_metadata_worst_case.metadata = metadata
    return get_article_metadata_worst_case.metadata

def get_article_urls_and_metadata_worst_case(homepage, metadata_wanted): # might be a bit slow
    """ Combines get_article_urls_wost_case() and get_article_metadata_worst_case() for a seamless 
    sequence of actions. The results are stored in a dataframe.
    """
    get_article_urls_worst_case(homepage)
    homepage_url = "https://www.zeit.de/"
    article_url_list = get_article_urls_worst_case.article_url_list
    article_list = []
    for article_url in article_url_list:
        if article_url != None:
            log.info(article_url)
            get_article_metadata_worst_case(article_url, metadata_wanted)
            metadata =  get_article_metadata_worst_case.metadata
            if len(metadata) != 0: # nested a bit too deep for my tastes, will refactor eventually
                article_list.append(metadata)
    log.info(f'{homepage_url}: {len(article_list)} articles have been found.\r')
    df = pd.DataFrame.from_dict(article_list)
    get_article_urls_and_metadata_worst_case.df = df
    return get_article_urls_and_metadata_worst_case.df

### Filter-related functions

def filter_urls(article_url_list):
    """ Filters out non-viable article URLs through a whitelist.
    Criteria: url ends in word character (-> not a / ) or includes the current year"""
    article_url_list_clean = []
    year = time.strftime(r"%Y")
    for article in article_url_list:
        viable_article = re.search(fr"((/(\w+-)+\w+-\w+(\.html)?)|/-/\w+|{year})", article) # adjust regex so that /index end is kicked
        if viable_article:
            article_url_list_clean.append(article)
    log.info(f'Removed {(len(article_url_list)-len(article_url_list_clean))} URLs.')
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
    log.info(f'{homepage_url}: {len(article_list)} articles with metadata have been found.')
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
    log.info(f'{homepage_url}: {len(article_list)} articles with metadata have been found.\r')
    df = pd.DataFrame.from_dict(article_list)
    get_article_urls_and_metadata_worst_case.df = df
    return get_article_urls_and_metadata_worst_case.df

### Site specific functions

def accept_pur_abo_homepage(homepage_url, class_name):
    """ Finds the iFrame and the consent button and clicks on it, 
    waiting on the ZEIT homepage to load. Currently not compatible with GeckoDriver.
    Output is the source code of the page, as well as the driver.
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
        log.info(text)
    accept_pur_abo_homepage.driver = driver
    accept_pur_abo_homepage.text = text
    return  [accept_pur_abo_homepage.text, accept_pur_abo_homepage.driver]

def accept_pur_abo_article(article_url_list, class_name):
    """ Finds the iFrame and the consent button and clicks on it, 
    waiting on the first ZEIT article in the article list
    to load. Driver is not quit, so that further extraction can
    take place without repeat button-clicking. Currently not compatible 
    with GeckoDriver.Output is the source code of the page and the driver.
    """
    options = webdriver.ChromeOptions()
    options.add_argument('headless') # comment out if you want to see what's happening
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    driver.get(article_url_list[0])
    try:
        WebDriverWait(driver, 10).until(EC.frame_to_be_available_and_switch_to_it(0))
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, class_name))).click()
        driver.switch_to.default_content()
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body[data-page-type="article"]'))) 
        text = driver.page_source
    except TimeoutException:
        text = 'Element could not be found, connection timed out.'
        log.info(text)
    accept_pur_abo_article.driver = driver
    accept_pur_abo_article.text = text
    return  [accept_pur_abo_article.text, accept_pur_abo_article.driver]

def get_pur_abo_article_urls(homepage_url, class_name):
    """ Extracts the article URLs from the source code of the homepage.
    Closes the driver after extraction and outputs the article URL list.
    """
    try:
        accept_pur_abo_homepage(homepage_url, class_name)
        get_article_urls_worst_case(accept_pur_abo_homepage.text)
        article_url_list = get_article_urls_worst_case.article_url_list
        get_pur_abo_article_urls.article_url_list = article_url_list
        driver = accept_pur_abo_homepage.driver
        driver.quit()
    except:
        log.info('Unexpected error occured.')
    return get_pur_abo_article_urls.article_url_list

def get_pur_abo_article_urls_and_metadata(homepage_url, class_name, metadata_wanted):
    """ Extracts the article URLs and metadata, relying on two successive 
    selenium webdriver executions. Outputs the dataframe of article URLs
    and metadata.
    """
    article_url_list = get_article_urls_worst_case.article_url_list
    accept_pur_abo_homepage(homepage_url, class_name)
    homepage_url = "https://www.zeit.de/"
    get_article_urls_worst_case(accept_pur_abo_homepage.text)
    article_url_list = get_article_urls_worst_case.article_url_list
    article_list = []
    driver = accept_pur_abo_homepage.driver
    driver.quit()
    accept_pur_abo_article(article_url_list,class_name)
    driver = accept_pur_abo_article.driver
    for article_url in article_url_list:
        if article_url != None:
            driver.get(article_url)
            article_page_source = driver.page_source
            get_article_metadata_worst_case(article_page_source, metadata_wanted)
            metadata =  get_article_metadata_worst_case.metadata
            if len(metadata) != 0: # nested a bit too deep for my tastes, will refactor eventually
                article_list.append(metadata)
    log.info(f'{homepage_url}: {len(article_list)} articles with metadata have been found.\r')
    driver.quit()
    df = pd.DataFrame.from_dict(article_list)
    get_pur_abo_article_urls_and_metadata.df = df
    return get_pur_abo_article_urls_and_metadata.df

def get_pur_abo_filtered_article_urls_and_metadata(homepage_url, class_name, metadata_wanted):
    """ Extracts the article URLs and metadata, relying on two successive 
    selenium webdriver executions. URLs are filtered before metadata is 
    extracted. Outputs the dataframe of article URLs and metadata.
    """
    accept_pur_abo_homepage(homepage_url, class_name)
    homepage_url = "https://www.zeit.de/"
    get_article_urls_worst_case(accept_pur_abo_homepage.text)
    article_url_list = get_article_urls_worst_case.article_url_list
    driver = accept_pur_abo_homepage.driver
    driver.quit()
    article_url_list_clean = filter_urls(article_url_list)
    article_list = []
    accept_pur_abo_article(article_url_list_clean,class_name)
    driver = accept_pur_abo_article.driver
    for article_url in article_url_list_clean:
        if article_url != None:
            driver.get(article_url)
            article_page_source = driver.page_source
            get_article_metadata_worst_case(article_page_source, metadata_wanted)
            metadata =  get_article_metadata_worst_case.metadata
            if len(metadata) != 0: # nested a bit too deep for my tastes, will refactor eventually
                article_list.append(metadata)
    log.info(f'{homepage_url}: {len(article_list)} articles have been found.\r')
    driver.quit()
    df = pd.DataFrame.from_dict(article_list)
    get_pur_abo_filtered_article_urls_and_metadata.df = df
    return get_pur_abo_filtered_article_urls_and_metadata.df

### Export

def export_dataframe(df, homepage_url, output_folder):
    """ Exports a given dataframe, naming it based on datetime and homepage url.
    """
    try:
        df_name = re.search(r"\..+?\.",f"{homepage_url}").group(0)
        df_name = df_name.replace(".","") 
        timestr = time.strftime(r"%Y%m%d-%H%M")
        df_path = f"{output_folder}/{timestr}-"+f"{df_name}"+f".csv"
        df.to_csv(df_path, index=False, mode='a')
        export_dataframe.df_path = df_path
    except:
        log.info('Unexpected error occurred.')
    return export_dataframe.df_path

### Click

## BEST CASE 

@cli.command(help='[BEST CASE] - Retrieves article URLs from homepage URL in the best case pipeline.')
@click.option('-u','--homepage-url',
              help='This is the URL you extract the article URLs from.')
def get_articles_bestcase(homepage_url):
    get_article_urls_best_case(homepage_url)
    #article_url_list = get_article_urls_best_case.article_url_list
     
@cli.command(help="[BEST CASE] - Retrieves metadata from an article URL in the best case pipeline.")
@click.option('-a', '--article-url',
              help='This is the article URL you extract metadata from.')
@click.option('-m', '--metadata-wanted', default="['title', 'date', 'url', 'description']",
              help='This is the metadata you want from the article, put in as a python list of strings.')
def get_metadata_bestcase(article_url, metadata_wanted):
    get_article_metadata_best_case(article_url, metadata_wanted)

@cli.command(help="[BEST CASE] - Retrieves metadata from an article URL in the best case pipeline.")
@click.option('-u','--homepage-url',
              help='This is the URL you extract the article URLs from.')
@click.option('-m', '--metadata-wanted', default="['title', 'date', 'url', 'description']",
              help='This is the metadata you want from the article, put in as a python list of strings.')
def get_both_bestcase(homepage_url, metadata_wanted):
    get_article_urls_and_metadata_best_case(homepage_url, metadata_wanted)

## WORST CASE

@cli.command(help="[WORST CASE] - Retrieves article URLs from homepage URL in the worst case pipeline.")
@click.option('-p', '--homepage',
              help='This is the URL or source code you extract the article URLs from.')
def get_articles_worstcase(homepage_url):
    get_article_urls_worst_case(homepage)

@cli.command(help="[WORST CASE] - Retrieves metadata from an article URL in the worst case pipeline.")
@click.option('-a', '--article-url',
              help='This is the article URL you extract metadata from.')
@click.option('-m', '--metadata-wanted', default="['title', 'date', 'url', 'description']",
              help='This is the metadata you want from the article, put in as a python list of strings.')
def get_metadata_worstcase(article_url, metadata_wanted):
    get_article_metadata_worst_case(article_url, metadata_wanted)

@cli.command(help="[WORST CASE] - Retrieves metadata from an article URL in the worst case pipeline.")
@click.option('-u','--homepage-url',
              help='This is the URL you extract the article URLs from.')
@click.option('-m', '--metadata-wanted', default="['title', 'date', 'url', 'description']",
              help='This is the metadata you want from the article, put in as a python list of strings.')
def get_both_worstcase(homepage_url, metadata_wanted):
    get_article_urls_and_metadata_worst_case(homepage_url, metadata_wanted)

## FILTERED CONTENT

@cli.command(help="Filters nonviable URLs out of article URL list.")
@click.option('-l', '--article-url-list',
             help='This is the list of article URLs to be filtered')
def filter_articles(article_url_list):
    filter_urls(article_url_list)

@cli.command(help='[FILTERED] [BEST CASE] - Filters nonviable URLs out of article list retrieved from a homepage URL, '
                'then extracts article metadata in the best case pipeline.')
@click.option('-u', '--homepage-url',
              help='This is the URL you extract the article URLs from.')
@click.option('-m', '--metadata-wanted', default="['title', 'date', 'url', 'description']",
              help='This is the metadata you want from the article, put in as a python list of strings.')
def filter_both_bestcase(homepage_url, metadata_wanted):
    get_filtered_article_urls_and_metadata_best_case(homepage_url,metadata_wanted)

@cli.command(help='[FILTERED] [WORST CASE] - Filters nonviable URLs out of article list retrieved from a homepage URL, '
                'then extracts article metadata in the worst case pipeline.')
@click.option('-u', '--homepage-url',
              help='This is the URL you extract the article URLs from.')
@click.option('-m', '--metadata-wanted', default="['title', 'date', 'url', 'description']",
              help='This is the metadata you want from the article, put in as a python list of strings.')
def filter_both_worstcase():
    get_filtered_article_urls_and_metadata_worst_case(homepage_url, metadata_wanted)

# Explain the Pur Abo better in this help text:
@cli.command(help='Presses the consent button on the homepage of a website with a so-called "Pur Abo".')
@click.option('-u', '--homepage-url',
              help='This is the URL you extract the article URLs from.')
@click.option('-c', '--class-name', default='sp_choice_type_11',
              help='This is the class name of the consent button. If no name is given, '
              'newsfeedback uses the class name used by ZEIT Online for their consent button.')
def consent_button_homepage(homepage_url, class_name):
    accept_pur_abo_homepage(homepage_url, class_name)

@cli.command(help='Presses the consent button before retrieving article metadata.')
@click.option('-l', '--article-url-list',
              help='This is the list of article URLs retrieved from the homepage.')
@click.option('-c', '--class-name', default='sp_choice_type_11',
              help='This is the class name of the consent button. If no name is given, '
              'newsfeedback uses the class name used by ZEIT Online for their consent button.')
def consent_button_article(article_url_list, class_name):
    accept_pur_abo_article(article_url_list, class_name)

@cli.command(help='Retrieves article URLs from a homepage with a consent button barrier.')
@click.option('-u', '--homepage-url',
              help='This is the URL you extract the article URLs from.')
@click.option('-c', '--class-name', default='sp_choice_type_11',
              help='This is the class name of the consent button. If no name is given, '
              'newsfeedback uses the class name used by ZEIT Online for their consent button.')
def consent_articles(homepage_url, class_name):
    get_pur_abo_article_urls(homepage_url, class_name)

@cli.command(help='Retrieves article URLs and metadata from a homepage with a consent button barrier.')
@click.option('-u', '--homepage-url',
              help='This is the URL you extract the article URLs from.')
@click.option('-c', '--class-name', default='sp_choice_type_11',
              help='This is the class name of the consent button. If no name is given, '
              'newsfeedback uses the class name used by ZEIT Online for their consent button.')
@click.option('-m', '--metadata-wanted', default="['title', 'date', 'url', 'description']",
              help='This is the metadata you want from the article, put in as a python list of strings.')
def consent_both(homepage_url, class_name, metadata_wanted):
    get_pur_abo_article_urls_and_metadata(homepage_url, class_name, metadata_wanted)

@cli.command(help='[FILTERED] - Retrieves article URLs and metadata from a homepage with a consent button barrier.')
@click.option('-u', '--homepage-url',
              help='This is the URL you extract the article URLs from.')
@click.option('-c', '--class-name', default='sp_choice_type_11',
              help='This is the class name of the consent button. If no name is given, '
              'newsfeedback uses the class name used by ZEIT Online for their consent button.')
@click.option('-m', '--metadata-wanted', default="['title', 'date', 'url', 'description']",
              help='This is the metadata you want from the article, put in as a python list of strings.')
def filter_consent_both(homepage_url, class_name, metadata_wanted):
    get_pur_abo_filtered_article_urls_and_metadata(homepage_url, class_name, metadata_wanted)

'''@cli.command(help='Exports the dataframe created in the pipeline.')
@click.option('-d', '--dataframe',
              help='The dataframe you have created.')
@click.option('-u', '--homepage-url',
              help='This is the URL you extract the article URLs from.')
@click.option('-o', '--output-folder', default='newsfeedback/output',
              help="The folder in which your exported dataframe is stored. Defaults to newsfeedback's output folder.")
def export_result()'''


if __name__ == "main":
    cli()