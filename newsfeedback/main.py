import trafilatura, click, re, time, yaml, os, schedule
import pandas as pd
from pathlib import Path
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

#log.add(sys.stderr, format = "<red>[{level}]</red> : <green>{message}</green> @ {time}", colorize=True, level="ERROR")

@click.group()
def cli():
    pass


def retrieve_config(type_config):
    directory = Path().resolve()
    path_user_metadata_config = directory/"user_metadata_config.yaml"
    path_default_metadata_config = directory/"newsfeedback"/"defaults"/"default_metadata_config.yaml"
    path_user_homepage_config = directory/"user_homepage_config.yaml"
    path_default_homepage_config = directory/"newsfeedback"/"defaults"/"default_homepage_config.yaml"

    if type_config == "metadata":
        if Path(path_user_metadata_config).exists():
            config_file = Path(path_user_metadata_config)
            log.info(f"Using the user-generated {type_config} config.")
        else:
            config_file = Path(path_default_metadata_config)
            log.info(f"Using the default {type_config} config.")
    elif type_config == "homepage":
        if Path(path_user_homepage_config).exists():
            config_file = Path(path_user_homepage_config)
            log.info(f"Using the user-generated {type_config} config.")
        else:
            config_file = Path(path_default_homepage_config)
            log.info(f"Using the default {type_config} config.")
    with config_file.open() as yamlfile:
        data = yaml.load(yamlfile, Loader=yaml.FullLoader)
        return data


### TRAFILATURA PIPELINE

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

def get_article_metadata_chain_trafilatura_pipeline(article_url_list):
    metadata_config = retrieve_config("metadata")
    metadata_wanted = [k for k,v in metadata_config.items() if v == True]
    metadata_wanted.append('datetime')
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
            datetime = time.strftime(r"%Y%m%d-%H%M")
            datetime_column = {'datetime':datetime}
            metadata.update(datetime_column)
        else:
            metadata = []
            #log.error(f'{article_url}: No metadata was found.')
        article_list.append(metadata)
    try:
        df = pd.DataFrame(article_list, columns = metadata_wanted)
        log.info(f'{df.shape[0]} articles with metadata were found.')
    except ValueError:
        df = pd.DataFrame(columns=metadata_wanted)
        log.error(f'No articles with metadata were found.')
    return df

### BEAUTIFULSOUP PIPELINE

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

def get_article_metadata_chain_bs_pipeline(article_url_list):
    metadata_config = retrieve_config("metadata")
    metadata_wanted = [k for k,v in metadata_config.items() if v == True]
    article_list = []
    metadata_wanted.append('datetime')

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
                datetime = time.strftime(r"%Y%m%d-%H%M")
                datetime_column = {'datetime':datetime}
                metadata.update(datetime_column)
            else:
                metadata = {}
                #log.error(f'{article}: No metadata was found.')
        else:  
            metadata = {}
            #log.error(f'{article}: No metadata was found.')
        article_list.append(metadata)
    df = pd.DataFrame(article_list, columns = metadata_wanted)
    if df.shape[0] != 0:
        log.info(f'{df.shape[0]} articles with metadata were found.')
    else:
        log.error(f'No articles with metadata were found.')
    return df


### PUR ABO PIPELINE

def accept_pur_abo_homepage(homepage_url, class_name):
    options = webdriver.ChromeOptions()
    options.add_argument('headless') # comment out if you want to see what's happening
    options.add_argument('--log-level=3')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
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
        text = 'Element could not be found, connection timed out.'
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
    options.add_argument('--log-level=3')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
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
    metadata_config = retrieve_config("metadata")
    metadata_wanted = [k for k,v in metadata_config.items() if v == True]
    metadata_wanted.append('datetime')
    for article_url in article_url_list:
        if article_url != None:
            driver.get(article_url)
            article_page_source = driver.page_source
            if len(article_page_source) < 300:
                downloaded = trafilatura.fetch_url(article_page_source)
            else:
                downloaded = article_page_source
            if downloaded != None:
                
                metadata = trafilatura.bare_extraction(downloaded, only_with_metadata=True, include_links=True)
                if metadata != None:
                    dict_keys = list(metadata.keys())
                    dict_keys_to_pop = [key for key in dict_keys if key not in metadata_wanted]
                    if len(dict_keys_to_pop) != 0:
                        for key in dict_keys_to_pop: 
                            metadata.pop(key, None)
                    else:
                        metadata = metadata
                    datetime = time.strftime(r"%Y%m%d-%H%M")
                    datetime_column = {'datetime':datetime}
                    metadata.update(datetime_column)
                    #log.info(f'Metadata was found.')  
                else:
                    metadata = {}
                    #log.error(f'No metadata was found.')
            else:  
                metadata = {}
                #log.error(f'No metadata was found.')
            if len(metadata) != 0: # nested a bit too deep for my tastes, will refactor eventually
                article_list.append(metadata)
    if len(article_list) != 0:
        log.info(f'{homepage_url}: {len(article_list)} articles with metadata have been found.\r')
    else:
        log.error(f'{homepage_url}: No articles with metadata were found.')
    driver.quit()
    df = pd.DataFrame.from_dict(article_list)
    return df

### Filter-related functions

def filter_urls(article_url_list, filter_choice):
    if filter_choice == 'on':
        filtered_url_list = []
        year = time.strftime(r"%Y")
        for article in article_url_list:
            viable_article = re.search(fr"((/(\w+-)+\w+-\w+(\.html)?)|/-/\w+|{year})", article) # adjust regex so that /index end is kicked
            if viable_article:
                filtered_url_list.append(article)
        removed = (len(article_url_list)-len(filtered_url_list))
        if removed != 0:
            log.info(f'Removed {removed} URLs.')
        else:
            log.error(f'Removed no URLs.')
    else:
        filtered_url_list = article_url_list
        log.info('Removed no URLs, as intended.')
    return filtered_url_list

### Export

def export_dataframe(df, homepage_url, output_folder):
    df_name = re.search(r"\..+?\.",f"{homepage_url}").group(0)
    df_name = df_name.replace(".","") 
    timestr = time.strftime(r"%Y%m%d-%H%M")
    output_folder = Path(output_folder)
    output_subfolder = (output_folder/df_name)
    Path(output_subfolder).mkdir(exist_ok=True)
    try:
        df_path = Path(f"{output_subfolder}/{timestr}-{df_name}.csv")
        df.to_csv(df_path, index=False, mode='a')
        log.info(f'File generated at: {df_path}')
    except:
        log.error('Unexpected error occurred. File could not be generated.')
    return df_path

### CHAINED PIPELINES

def chained_trafilatura_pipeline(homepage_url, filter_choice, output_folder):
    article_url_list = get_article_urls_trafilatura_pipeline(homepage_url)
    filtered_url_list = filter_urls(article_url_list, filter_choice)
    df = get_article_metadata_chain_trafilatura_pipeline(filtered_url_list)
    df_path = export_dataframe(df, homepage_url, output_folder)
    
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
    article_url_list = get_article_urls_bs_pipeline(homepage_url)
    filtered_url_list = filter_urls(article_url_list, filter_choice)
    df = get_article_metadata_chain_bs_pipeline(filtered_url_list)
    df_path = export_dataframe(df, homepage_url, output_folder)
                  
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

### CONFIG RELATED FUNCTIONS

def get_pipeline_from_config(homepage_url, output_folder):
    homepage_config = retrieve_config('homepage')
    data = homepage_config.get(homepage_url)
    if data:
        pipeline = data.get('pipeline')
        filter_option = data.get('filter')
        log.info(f'{homepage_url} uses the {pipeline} pipeline and has filtering turned {filter_option}.')
        if pipeline == 'trafilatura':
            chained_trafilatura_pipeline(homepage_url, filter_option, output_folder)
        elif pipeline == 'beautifulsoup':
            chained_beautifulsoup_pipeline(homepage_url, filter_option, output_folder)
        elif pipeline == 'purabo':
            chained_purabo_pipeline(homepage_url, 'sp_choice_type_11', filter_option, output_folder)
        else:
            log.error('Please check the pipeline information given for this URL.')
    else:
        log.error("Please check that the URL you have given matches the required structure (https://www.name.de/) "
                  "and has already been added to the config. Otherwise add it to the config via the CLI "
                  "with 'newsfeedback add-homepage-url'. Data may be coming from an unintended config (default/custom). ")
    
@cli.command(help="Chooses and executes the pipeline saved in the config file.")
@click.option('-u','--homepage-url',
              help='This is the URL you extract the article URLs from.')
@click.option('-o', '--output-folder', default='newsfeedback/output',
              help="The folder in which your exported dataframe is stored. Defaults to newsfeedback's output folder.")

def pipeline_picker(homepage_url, output_folder):

    get_pipeline_from_config(homepage_url, output_folder)

def write_in_config(homepage_url, chosen_pipeline, filter_option):
    if chosen_pipeline == '1':
        chosen_pipeline = 'trafilatura'
    elif chosen_pipeline == '2':
        chosen_pipeline = 'beautifulsoup'
    elif chosen_pipeline == '3':
        chosen_pipeline = 'purabo'
    else:
        chosen_pipeline = 'error'

    new_homepage = {
            homepage_url: {
                'pipeline' : chosen_pipeline,
                'filter' : filter_option.replace("'","")
            }
        }
    

    with open("user_homepage_config.yaml", 'a+') as yamlfile:
        yaml.dump(new_homepage, yamlfile)


@cli.command(help="Adds a new homepage to the config file.")
@click.option('-u', '--homepage-url',
              prompt="Your homepage URL (required format: https://www.name.de/) ",
              help="The homepage URL you wish to add (i.e. https://www.spiegel.de/) to the config file. "
              "Please follow the example URL structure to reduce the potential for duplicates. ")
@click.option('-p', '--chosen-pipeline',
              prompt="Pick one of the available pipelines: 1 - trafilatura, 2 - beautifulsoup, 3 - purabo ",
              help="The pipeline through which your article URLs and metadata are extracted. They are named for "
              "the packages and libraries primarily used in extraction. \n [trafilatura] has a higher error rate but "
              "no need for extra filtering. [beautifulsoup] works for all webpages, but requires further filtering. "
              "If a website has a so-called Pur Abo (i.e. ZEIT online), the [purabo] is the only viable option.")
@click.option('-f', '--filter-option',
              prompt="Decide if you want filtering. Type 'on' or 'off'",
              help="Filtering is recommended for the beautifulsoup and purabo pipelines, "
              "but not for the trafilatura pipelines. It roughly filters out nonviable URLs "
              "retrieved in broader extraction processes.")
def add_homepage_url(homepage_url, chosen_pipeline, filter_option):
    write_in_config(homepage_url, chosen_pipeline, filter_option)

def initiate_data_collection(output_folder):
    homepage_config = retrieve_config('homepage')
    homepage_url_list = list(homepage_config.keys())
    for homepage_url in homepage_url_list:
        get_pipeline_from_config(homepage_url, output_folder)

@cli.command(help="Runs the full pipeline for the URLs saveds in either the user or default "
              "config file on schedule.")
@click.option('-t', '--hour', default='6',
              help='Run data extraction once every X hours. This is X, but defaults to 6.')
@click.option('-o', '--output-folder', default='newsfeedback/output',
              help="The folder in which your exported dataframe is stored. Defaults to newsfeedback's output folder.")
def get_data(hour, output_folder):
    schedule.every(int(hour)).hours.do(initiate_data_collection, output_folder)
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "main":
    cli()