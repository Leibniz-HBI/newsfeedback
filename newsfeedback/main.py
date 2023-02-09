import trafilatura, click, re, time, sys, yaml, os
import pandas as pd
from trafilatura import feeds
from loguru import logger as log
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException

log.add(sys.stderr, format = "<red>[{level}]</red> : <green>{message}</green> @ {time}", colorize=True, level="ERROR")

@click.group()
def cli():
    pass


def retrieve_config(type_config):
    if type_config == "metadata":
        if os.path.isfile("newsfeedback/user_metadata_config.yaml"):
            config_file = "newsfeedback/user_metadata_config.yaml"
        else:
            config_file = "newsfeedback/default_metadata_config.yaml"
    elif type_config == "website":
        pass
    with open(config_file, "r") as yamlfile:
        data = yaml.load(yamlfile, Loader=yaml.FullLoader)
        return data

### Best case functions

def get_article_urls_trafilatura_pipeline(homepage_url):
    article_url_list = feeds.find_feed_urls(homepage_url)
    if len(article_url_list) != 0:
        log.info(f'{homepage_url}: {len(article_url_list)} articles were found.\r')
    else:
        log.error(f'{homepage_url}: No articles were found.')
    return article_url_list

@cli.command(help='[TRAFILATURA PIPELINE] - Retrieves article URLs from homepage URL. Returns an article URL list.')
@click.option('-u','--homepage-url',
              help='This is the URL you extract the article URLs from. When using the BeautifulSoup pipeline, this can also be  HTML source code.')
def get_articles_trafilatura_pipeline(homepage_url):
    get_article_urls_trafilatura_pipeline(homepage_url)


def get_article_metadata_trafilatura_pipeline(article_url):
    metadata_config = retrieve_config("metadata")
    metadata_wanted = [k for k,v in metadata_config.items() if v == True]
    downloaded = trafilatura.fetch_url(article_url)
    metadata = trafilatura.bare_extraction(downloaded, only_with_metadata=True, include_links=True)
    if metadata is not None:
        dict_keys = list(metadata.keys())
        dict_keys_to_pop = [key for key in dict_keys if key not in metadata_wanted]
        if len(dict_keys_to_pop) != 0:
            for key in dict_keys_to_pop: 
                metadata.pop(key, None)
        else:
            metadata = metadata
        log.info(f'{article_url}: Metadata was found.')
    else:
        metadata = []
        log.error(f'{article_url}: No metadata was found.')
    return metadata

@cli.command(help="[TRAFILATURA PIPELINE] - Retrieves metadata from an article URL. Returns a dict of metadata.")
@click.option('-a', '--article-url',
              help='This is the article URL you extract metadata from.') 
def get_metadata_trafilatura_pipeline(article_url):
    get_article_metadata_trafilatura_pipeline(article_url)

def get_article_metadata_chain_trafilatura_pipeline(article_url_list):
    metadata_config = retrieve_config("metadata")
    metadata_wanted = [k for k,v in metadata_config.items() if v == True]
    article_list = []
    for article_url in article_url_list:
        downloaded = trafilatura.fetch_url(article_url)
        metadata = trafilatura.bare_extraction(downloaded, only_with_metadata=True, include_links=True)
        if metadata is not None:
            dict_keys = list(metadata.keys())
            dict_keys_to_pop = [key for key in dict_keys if key not in metadata_wanted]
            if len(dict_keys_to_pop) != 0:
                for key in dict_keys_to_pop: 
                    metadata.pop(key, None)
            else:
                metadata = metadata
            log.info(f'{article_url}: Metadata was found.')
        else:
            metadata = []
            log.error(f'{article_url}: No metadata was found.')
        article_list.append(metadata)
    df = pd.DataFrame(article_list, columns = metadata_wanted)
    if df.shape[0] != 0:
        log.info(f'{df.shape[0]} articles with metadata were found.')
    else:
        log.error(f'No articles with metadata were found.')
    return df

def get_article_urls_and_metadata_trafilatura_pipeline(homepage_url):
    article_url_list = get_article_urls_trafilatura_pipeline(homepage_url)
    article_list = []
    for article_url in article_url_list:
        metadata = get_article_metadata_trafilatura_pipeline(article_url)
        article_list.append(metadata)
    df = pd.DataFrame.from_dict(article_list)
    if df.shape[0] != 0:
        log.info(f'{homepage_url}: {df.shape[0]} articles with metadata were found.')
    else:
        log.error(f'{homepage_url}: No articles with metadata were found.')
    return df

@cli.command(help="[TRAFILATURA PIPELINE] - Retrieves metadata from an article URL. Exports resulting dataframe to output folder.")
@click.option('-u','--homepage-url',
              help='This is the URL you extract the article URLs from.')
@click.option('-o', '--output-folder', default='newsfeedback/output',
              help="The folder in which your exported dataframe is stored. Defaults to newsfeedback's output folder.")
def get_both_trafilatura_pipeline(homepage_url, output_folder):
    df = get_article_urls_and_metadata_trafilatura_pipeline(homepage_url)
    export_dataframe(df, homepage_url, output_folder)





### Worst case functions 
def get_article_urls_bs_pipeline(homepage):
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
    if len(article_url_list) != 0:
        log.info(f'{homepage_url}: {len(article_url_list)} links have been found.\r')
    else:
        log.error(f'{homepage_url}: No articles have been found. \r')
    return article_url_list

@cli.command(help="[BEAUTIFULSOUP PIPELINE] - Retrieves article URLs from homepage URL. Returns a list of article URLs")
@click.option('-u','--homepage-url',
              help='This is the URL you extract the article URLs from. When using the BeautifulSoup pipeline, this can also be  HTML source code.')
def get_articles_bs_pipeline(homepage_url):
    get_article_urls_bs_pipeline(homepage_url)


def get_article_metadata_bs_pipeline(article):
    if len(article) < 300:
        downloaded = trafilatura.fetch_url(article)
    else:
        downloaded = article
    if downloaded != None:
        metadata_config = retrieve_config("metadata")
        metadata_wanted = [k for k,v in metadata_config.items() if v == True]
        metadata = trafilatura.bare_extraction(downloaded, only_with_metadata=True, include_links=True)
        if metadata != None:
            dict_keys = list(metadata.keys())
            dict_keys_to_pop = [key for key in dict_keys if key not in metadata_wanted]
            if len(dict_keys_to_pop) != 0:
                for key in dict_keys_to_pop: 
                    metadata.pop(key, None)
            else:
                metadata = metadata
            log.info(f'Metadata was found.')  
        else:
            metadata = {}
            log.error(f'No metadata was found.')
    else:  
        metadata = {}
        log.error(f'No metadata was found.')
    return metadata

@cli.command(help="[BEAUTIFULSOUP PIPELINE] - Retrieves metadata from an article URL. Returns a dict of metadata.")
@click.option('-a', '--article-url',
              help='This is the article URL you extract metadata from.') 
def get_metadata_bs_pipeline(article_url):
    get_article_metadata_bs_pipeline(article_url)

def get_article_metadata_chain_bs_pipeline(article_url_list):
    metadata_config = retrieve_config("metadata")
    metadata_wanted = [k for k,v in metadata_config.items() if v == True]
    article_list = []
    for article in article_url_list:
        if len(article) < 300:
            downloaded = trafilatura.fetch_url(article)
        else:
            downloaded = article
        if downloaded != None:
            metadata_config = retrieve_config("metadata")
            metadata_wanted = [k for k,v in metadata_config.items() if v == True]
            metadata = trafilatura.bare_extraction(downloaded, only_with_metadata=True, include_links=True)
            if metadata != None:
                dict_keys = list(metadata.keys())
                dict_keys_to_pop = [key for key in dict_keys if key not in metadata_wanted]
                if len(dict_keys_to_pop) != 0:
                    for key in dict_keys_to_pop: 
                        metadata.pop(key, None)
                else:
                    metadata = metadata
                log.info(f'Metadata was found.')  
            else:
                metadata = {}
                log.error(f'No metadata was found.')
        else:  
            metadata = {}
            log.error(f'No metadata was found.')
        article_list.append(metadata)
    df = pd.DataFrame(article_list, columns = metadata_wanted)
    if df.shape[0] != 0:
        log.info(f'{df.shape[0]} articles with metadata were found.')
    else:
        log.error(f'No articles with metadata were found.')
    return df

def get_article_urls_and_metadata_bs_pipeline(homepage): # might be a bit slow
    article_url_list = get_article_urls_bs_pipeline(homepage)
    homepage_url = "https://www.zeit.de/"
    article_list = []
    for article_url in article_url_list:
        if article_url != None:
            log.info(article_url)
            metadata = get_article_metadata_bs_pipeline(article_url)
            if len(metadata) != 0: # nested a bit too deep for my tastes, will refactor eventually
                article_list.append(metadata)
    if (len(article_list)) != 0:
        log.info(f'{homepage_url}: {len(article_list)} articles have been found.\r')
    else:
        log.error(f'{homepage_url}: No articles have been found. \r')
    df = pd.DataFrame.from_dict(article_list)
    return df

@cli.command(help="[BEAUTIFULSOUP PIPELINE] - Retrieves metadata from article URLs in the BeautifulSoup pipeline. Exports resulting dataframe to output folder.")
@click.option('-u','--homepage-url',
              help='This is the URL you extract the article URLs from. When using the BeautifulSoup pipeline, this can also be  HTML source code.')
@click.option('-o', '--output-folder', default='newsfeedback/output',
              help="The folder in which your exported dataframe is stored. Defaults to newsfeedback's output folder.")

def get_both_bs_pipeline(homepage_url, output_folder):
    df = get_article_urls_and_metadata_bs_pipeline(homepage_url)
    export_dataframe(df, homepage_url, output_folder)


### Filter-related functions

def filter_urls(article_url_list, filter_choice):
    if filter_choice == 'on':
        returned_article_url_list = []
        year = time.strftime(r"%Y")
        for article in article_url_list:
            viable_article = re.search(fr"((/(\w+-)+\w+-\w+(\.html)?)|/-/\w+|{year})", article) # adjust regex so that /index end is kicked
            if viable_article:
                returned_article_url_list.append(article)
        removed = (len(article_url_list)-len(returned_article_url_list))
        if removed != 0:
            log.info(f'Removed {removed} URLs.')
        else:
            log.error(f'Removed no URLs.')
    else:
        returned_article_url_list = article_url_list
        log.info('Removed no URLs, as intended.')
    return returned_article_url_list

def get_filtered_article_urls(homepage_url):
    article_url_list = get_article_urls_bs_pipeline(homepage_url)
    article_url_list_clean = filter_urls(article_url_list, filter_choice='on')
    if len(article_url_list_clean) != 0:
        log.info(f'{homepage_url}: {len(article_url_list_clean)} viable URLs were found.')
    else:
        log.error(f'{homepage_url}: No viable articles were found.')
    return article_url_list_clean

@cli.command(help='[FILTERED] [BEAUTIFULSOUP PIPELINE]- Filters articles extracted from a homepage URL. Returns a filtered article URL list.')
@click.option('-u','--homepage-url',
              help='This is the URL you extract the article URLs from. When using the BeautifulSoup pipeline, this can also be  HTML source code.')
def filter_articles(homepage_url):
    get_filtered_article_urls(homepage_url)

def get_filtered_article_urls_and_metadata_trafilatura_pipeline(homepage_url):
    article_url_list = get_article_urls_trafilatura_pipeline(homepage_url)
    article_url_list_clean = filter_urls(article_url_list, filter_choice='on')
    article_list = []
    if len(article_url_list_clean) != 0:
        for article_url in article_url_list_clean:
            metadata = get_article_metadata_trafilatura_pipeline(article_url)
            article_list.append(metadata)
    df = pd.DataFrame.from_dict(article_list)
    if len(article_list) != 0:
        log.info(f'{homepage_url}: {len(article_list)} viable articles with metadata were found.')
    else:
        log.error(f'{homepage_url}: No viable articles with metadata were found.')
    return df

@cli.command(help='[FILTERED] [TRAFILATURA PIPELINE] - Filters nonviable URLs out of article list retrieved from a homepage URL, '
                'then extracts article metadata. Exports resulting dataframe to output folder.')
@click.option('-u','--homepage-url',
              help='This is the URL you extract the article URLs from. When using the BeautifulSoup pipeline, this can also be  HTML source code.')
@click.option('-o', '--output-folder', default='newsfeedback/output',
              help="The folder in which your exported dataframe is stored. Defaults to newsfeedback's output folder.")
def filter_both_trafilatura_pipeline(homepage_url, output_folder):
    df = get_filtered_article_urls_and_metadata_trafilatura_pipeline(homepage_url)
    export_dataframe(df, homepage_url, output_folder)

def get_filtered_article_urls_and_metadata_bs_pipeline(homepage_url):
    article_url_list = get_article_urls_bs_pipeline(homepage_url)
    article_url_list_clean = filter_urls(article_url_list, filter_choice='on')
    article_list = []
    for article_url in article_url_list_clean:
        if article_url != None:
            metadata = get_article_metadata_bs_pipeline(article_url)
            if len(metadata) != 0: # nested a bit too deep for my tastes, will refactor eventually
                article_list.append(metadata)
    if len(article_list) != 0:
        log.info(f'{homepage_url}: {len(article_list)} viable articles with metadata have been found.\r')
    else:
        log.error('No viable articles with metadata were found.')
    df = pd.DataFrame.from_dict(article_list)
    return df

@cli.command(help='[FILTERED] [BEAUTIFULSOUP PIPELINE] - Filters nonviable URLs out of article list retrieved from a homepage URL, '
                'then extracts article metadata. Exports resulting dataframe to output folder.')
@click.option('-u','--homepage-url',
              help='This is the URL you extract the article URLs from. When using the BeautifulSoup pipeline, this can also be  HTML source code.')
@click.option('-o', '--output-folder', default='newsfeedback/output',
              help="The folder in which your exported dataframe is stored. Defaults to newsfeedback's output folder.")
def filter_both_bs_pipeline(homepage_url, output_folder):
    df = get_filtered_article_urls_and_metadata_bs_pipeline(homepage_url)
    export_dataframe(df, homepage_url, output_folder)

### Site specific functions

def accept_pur_abo_homepage(homepage_url, class_name):
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
        log.info("The consent button was successfully clicked.")
    except TimeoutException:
        text = 'Element could not be found, connection timed out.' # text variable probably superfluous
        log.error(text)
    return text, driver

@cli.command(help='Presses the consent button on the homepage of a website with a so-called "Pur Abo".')
@click.option('-u','--homepage-url',
              help='This is the URL you extract the article URLs from. When using the BeautifulSoup pipeline, this can also be  HTML source code.')
@click.option('-c', '--class-name', default='sp_choice_type_11',
              help='This is the class name of the consent button. If no name is given, '
              'newsfeedback uses the class name used by ZEIT Online for their consent button.')
def consent_button_homepage(homepage_url, class_name):
    accept_pur_abo_homepage(homepage_url, class_name)


def accept_pur_abo_article(article_url_list, class_name):
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
        log.info("The consent button was successfully clicked.")
    except TimeoutException:
        text = 'Element could not be found, connection timed out.' # text variable probably superfluous
        log.error(text)
    return text, driver

@cli.command(help='Presses the consent button before retrieving article metadata.')
@click.option('-l', '--article-url-list',
              help='This is the list of article URLs retrieved from the homepage.')
@click.option('-c', '--class-name', default='sp_choice_type_11',
              help='This is the class name of the consent button. If no name is given, '
              'newsfeedback uses the class name used by ZEIT Online for their consent button.')
def consent_button_article(article_url_list, class_name):
    accept_pur_abo_article(article_url_list, class_name)


def get_pur_abo_article_urls(homepage_url, class_name):
    try:
        result_homepage = accept_pur_abo_homepage(homepage_url, class_name)
        text = result_homepage[0]
        article_url_list = get_article_urls_bs_pipeline(text)
        driver = result_homepage[1]
        driver.quit()
        log.info(f'{homepage_url}: {len(article_url_list)} articles were found.\r')
    except:
        log.error('Unexpected error occured.')
    return article_url_list

@cli.command(help='Retrieves article URLs from a homepage with a consent button barrier. Returns a list of article URLs.')
@click.option('-u','--homepage-url',
              help='This is the URL you extract the article URLs from. When using the BeautifulSoup pipeline, this can also be  HTML source code.')
@click.option('-c', '--class-name', default='sp_choice_type_11',
              help='This is the class name of the consent button. If no name is given, '
              'newsfeedback uses the class name used by ZEIT Online for their consent button.')
def consent_articles(homepage_url, class_name):
    get_pur_abo_article_urls(homepage_url, class_name)

def get_pur_abo_article_urls_chain(text, driver):
    try:
        article_url_list = []
        downloaded = text
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
        if len(article_url_list) != 0:
            log.info(f'{homepage_url}: {len(article_url_list)} links have been found.\r')
        else:
            log.error(f'{homepage_url}: No articles have been found. \r')
        driver.quit()
    except:
        log.error('Unexpected error occured.')
    return article_url_list

def get_pur_abo_article_metadata_chain(homepage_url, driver, article_url_list):
    article_list = []
    for article_url in article_url_list:
        if article_url != None:
            driver.get(article_url)
            article_page_source = driver.page_source
            metadata = get_article_metadata_bs_pipeline(article_page_source)
            if len(metadata) != 0: # nested a bit too deep for my tastes, will refactor eventually
                article_list.append(metadata)
    if len(article_list) != 0:
        log.info(f'{homepage_url}: {len(article_list)} articles with metadata have been found.\r')
    else:
        log.error(f'{homepage_url}: No articles with metadata were found.')
    driver.quit()
    df = pd.DataFrame.from_dict(article_list)
    return df

def get_pur_abo_article_urls_and_metadata(homepage_url, class_name):
    result_homepage = accept_pur_abo_homepage(homepage_url, class_name)
    text = result_homepage[0]
    article_url_list = get_article_urls_bs_pipeline(text)
    homepage_url = "https://www.zeit.de/"
    article_list = []
    driver = result_homepage[1]
    driver.quit()
    result_article = accept_pur_abo_article(article_url_list,class_name)
    driver = result_article[1]
    for article_url in article_url_list:
        if article_url != None:
            driver.get(article_url)
            article_page_source = driver.page_source
            metadata = get_article_metadata_bs_pipeline(article_page_source)
            if len(metadata) != 0: # nested a bit too deep for my tastes, will refactor eventually
                article_list.append(metadata)
    if len(article_list) != 0:
        log.info(f'{homepage_url}: {len(article_list)} articles with metadata have been found.\r')
    else:
        log.error(f'{homepage_url}: No articles with metadata were found.')
    driver.quit()
    df = pd.DataFrame.from_dict(article_list)
    return df

@cli.command(help='Retrieves article URLs and metadata from a homepage with a consent button barrier. Exports resulting dataframe to output folder.')
@click.option('-u','--homepage-url',
              help='This is the URL you extract the article URLs from. When using the BeautifulSoup pipeline, this can also be  HTML source code.')
@click.option('-c', '--class-name', default='sp_choice_type_11',
              help='This is the class name of the consent button. If no name is given, '
              'newsfeedback uses the class name used by ZEIT Online for their consent button.')
@click.option('-o', '--output-folder', default='newsfeedback/output',
              help="The folder in which your exported dataframe is stored. Defaults to newsfeedback's output folder.")

def consent_both(homepage_url, class_name, output_folder):
    df = get_pur_abo_article_urls_and_metadata(homepage_url, class_name)
    export_dataframe(df, homepage_url, output_folder)

def get_pur_abo_filtered_article_urls_and_metadata(homepage_url, class_name):
    result_homepage = accept_pur_abo_homepage(homepage_url, class_name)
    homepage_url = "https://www.zeit.de/"
    text = result_homepage[0]
    article_url_list = get_article_urls_bs_pipeline(text)
    driver = result_homepage[1]
    driver.quit()
    article_url_list_clean = filter_urls(article_url_list)
    article_list = []
    result_article = accept_pur_abo_article(article_url_list_clean,class_name)
    driver = result_article[1]
    for article_url in article_url_list_clean:
        if article_url != None:
            driver.get(article_url)
            article_page_source = driver.page_source
            metadata = get_article_metadata_bs_pipeline(article_page_source)
            if len(metadata) != 0: # nested a bit too deep for my tastes, will refactor eventually
                article_list.append(metadata)
    if len(article_list) != 0:
        log.info(f'{homepage_url}: {len(article_list)} viable articles with metadata have been found.\r')
    else:
        log.error(f'{homepage_url}: No viable articles with metadata were found.')
        driver.quit()
    df = pd.DataFrame.from_dict(article_list)
    return df

@cli.command(help='[FILTERED] - Retrieves article URLs and metadata from a homepage with a consent button barrier. Exports resulting dataframe to output folder.')
@click.option('-u','--homepage-url',
              help='This is the URL you extract the article URLs from. When using the BeautifulSoup pipeline, this can also be  HTML source code.')
@click.option('-c', '--class-name', default='sp_choice_type_11',
              help='This is the class name of the consent button. If no name is given, '
              'newsfeedback uses the class name used by ZEIT Online for their consent button.')
@click.option('-o', '--output-folder', default='newsfeedback/output',
              help="The folder in which your exported dataframe is stored. Defaults to newsfeedback's output folder.")

def filter_consent_both(homepage_url, class_name, output_folder):
    df = get_pur_abo_filtered_article_urls_and_metadata(homepage_url, class_name)
    export_dataframe(df, homepage_url, output_folder)
### Export

def export_dataframe(df, homepage_url, output_folder):
    try:
        df_name = re.search(r"\..+?\.",f"{homepage_url}").group(0)
        df_name = df_name.replace(".","") 
        timestr = time.strftime(r"%Y%m%d-%H%M")
        df_path = f"{output_folder}/{timestr}-"+f"{df_name}"+f".csv"
        df.to_csv(df_path, index=False, mode='a')
        log.info(f'File generated at: {df_path}')
    except:
        log.error('Unexpected error occurred.')
    return df_path

### CHAINED PIPELINES

def chained_trafilatura_pipeline(homepage_url, filter_choice, output_folder):
    df_path = export_dataframe(get_article_metadata_chain_trafilatura_pipeline(filter_urls(get_article_urls_trafilatura_pipeline(homepage_url), filter_choice)), homepage_url, output_folder)
    return df_path

@cli.command(help="[TRAFILATURA PIPELINE] - Executes the complete trafilatura pipeline.")
@click.option('-u','--homepage-url',
              help='This is the URL you extract the article URLs from.')
@click.option('-f', '--filter-choice',
              help="Whether you want to filter results or not. Either 'on' or 'off'.")
@click.option('-o', '--output-folder', default='newsfeedback/output',
              help="The folder in which your exported dataframe is stored. Defaults to newsfeedback's output folder.")
def trafilatura_pipeline(homepage_url, filter_choice, output_folder):
    chained_trafilatura_pipeline(homepage_url, filter_choice, output_folder)

def chained_beautifulsoup_pipeline(homepage_url, filter_choice, output_folder):
    df_path = export_dataframe(get_article_metadata_chain_bs_pipeline(filter_urls(get_article_urls_bs_pipeline(homepage_url), filter_choice)), homepage_url, output_folder)
    return df_path

@cli.command(help="[BEAUTIFULSOUP PIPELINE] - Executes the complete beautifulsoup pipeline.")
@click.option('-u','--homepage-url',
              help='This is the URL you extract the article URLs from.')
@click.option('-f', '--filter-choice',
              help="Whether you want to filter results or not. Either 'on' or 'off'.")
@click.option('-o', '--output-folder', default='newsfeedback/output',
              help="The folder in which your exported dataframe is stored. Defaults to newsfeedback's output folder.")
def beautifulsoup_pipeline(homepage_url, filter_choice, output_folder):
    chained_beautifulsoup_pipeline(homepage_url, filter_choice, output_folder)

def chained_purabo_pipeline(homepage_url, class_name, filter_choice, output_folder):
    (text, driver) = accept_pur_abo_homepage(homepage_url, class_name)
    article_url_list = get_pur_abo_article_urls_chain(text, driver)
    returned_article_url_list = filter_urls(article_url_list, filter_choice)
    driver.quit()
    (text, driver) = accept_pur_abo_article(returned_article_url_list, class_name)
    df = get_pur_abo_article_metadata_chain(homepage_url, driver, returned_article_url_list)
    export_dataframe(df, homepage_url, output_folder)
    #df_path = export_dataframe(get_article_metadata_chain_bs_pipeline(filter_urls(consent_button_article_chain(get_article_urls_bs_pipeline(consent_button_homepage_chain(homepage_url))), filter_choice)), homepage_url, output_folder)

@cli.command(help="[PURABO PIPELINE] - Executes the complete pur abo pipeline.")
@click.option('-u','--homepage-url',
              help='This is the URL you extract the article URLs from.')
@click.option('-c', '--class-name', default='sp_choice_type_11',
              help='This is the class name of the consent button. If no name is given, '
              'newsfeedback uses the class name used by ZEIT Online for their consent button.')
@click.option('-f', '--filter-choice',
              help="Whether you want to filter results or not. Either 'on' or 'off'.")
@click.option('-o', '--output-folder', default='newsfeedback/output',
              help="The folder in which your exported dataframe is stored. Defaults to newsfeedback's output folder.")
def purabo_pipeline(homepage_url, class_name, filter_choice, output_folder):
    chained_purabo_pipeline(homepage_url, class_name, filter_choice, output_folder)


if __name__ == "main":
    cli()