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


def retrieve_config(type_config, tmp_path=False):
    directory = Path().resolve()
    path_user_metadata_config = directory/"user_metadata_config.yaml"
    path_default_metadata_config = directory/"newsfeedback"/"defaults"/"default_metadata_config.yaml"
    path_user_homepage_config = directory/"user_homepage_config.yaml"
    path_default_homepage_config = directory/"newsfeedback"/"defaults"/"default_homepage_config.yaml"
    if tmp_path:
        path_tmp_metadata_config = tmp_path/"tmp_metadata_config.yaml"
        path_tmp_homepage_config = tmp_path/"tmp_homepage_config.yaml"

    if type_config == "metadata":
        if Path(path_user_metadata_config).exists():
            config_file = Path(path_user_metadata_config)
            log.info(f"Using the user-generated {type_config} config at {config_file}.")
        else:
            config_file = Path(path_default_metadata_config)
            log.info(f"Using the default {type_config} config at {config_file}.")
    elif type_config == "metadata_default":
        config_file = Path(path_default_metadata_config)
        log.info(f"Using the default {type_config} config at {config_file}.")
    elif type_config == "metadata_test":
        config_file = Path(path_tmp_metadata_config)
        config_file.write_bytes(path_default_metadata_config.read_bytes())
        log.info(f"Using the default {type_config} config at {config_file}.")

    elif type_config == "homepage":
        if Path(path_user_homepage_config).exists():
            config_file = Path(path_user_homepage_config)
            log.info(f"Using the user-generated {type_config} config at {config_file}.")
        else:
            config_file = Path(path_default_homepage_config)
            log.info(f"Using the default {type_config} config at {config_file}.")
    elif type_config == "homepage_default":
        config_file = Path(path_default_homepage_config)
        log.info(f"Using the default {type_config} config at {config_file}.")
    elif type_config == "homepage_test":
        config_file = Path(path_tmp_homepage_config)
        config_file.write_bytes(path_default_homepage_config.read_bytes())
        log.info(f"Using the default {type_config} config at {config_file}.")
  
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

'''@cli.command(help='[TRAFILATURA PIPELINE] - Retrieves article URLs from homepage URL. Returns an article URL list.')
@click.option('-u','--homepage-url',
              help='This is the URL you extract the article URLs from. When using the BeautifulSoup pipeline, this can also be  HTML source code.')
def get_articles_trafilatura_pipeline(homepage_url):
    get_article_urls_trafilatura_pipeline(homepage_url)'''

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
        if len(metadata) != 0:
            for k,v in metadata.items():
                        if k == 'text':
                            v_new = v.replace('"',"“").replace("'","’").replace("\n","[¶]") # will this cause issues with URLs later? maybe!
                            v = f'"{v_new}"'
                            k_v_new ={k:v}
                            metadata.update(k_v_new)
                        elif k == 'comments':
                            v_new = v.replace('"',"“").replace("'","’").replace("\n","[¶]") # will this cause issues with URLs later? maybe!
                            v = f'"{v_new}"'
                            k_v_new ={k:v}
                            metadata.update(k_v_new)
                        else:
                            pass        
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

'''@cli.command(help="[BEAUTIFULSOUP PIPELINE] - Retrieves article URLs from homepage URL. Returns a list of article URLs")
@click.option('-u','--homepage-url',
              help='This is the URL you extract the article URLs from. When using the BeautifulSoup pipeline, this can also be  HTML source code.')
def get_articles_bs_pipeline(homepage_url):
    get_article_urls_bs_pipeline(homepage_url)'''

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
            metadata = trafilatura.bare_extraction(downloaded, only_with_metadata=True, include_links=True, include_comments=True)
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
        else:  
            metadata = {}
        if len(metadata) != 0:
            for k,v in metadata.items():
                        if k == 'text':
                            v_new = v.replace('"',"“").replace("'","’").replace("\n","[¶]") # will this cause issues with URLs later? maybe!
                            v = f'"{v_new}"'
                            k_v_new ={k:v}
                            metadata.update(k_v_new)
                        elif k == 'comments':
                            v_new = v.replace('"',"“").replace("'","’").replace("\n","[¶]") # will this cause issues with URLs later? maybe!
                            v = f'"{v_new}"'
                            k_v_new ={k:v}
                            metadata.update(k_v_new)
                        else:
                            pass
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
    options.add_argument('--lang=en')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    driver.delete_all_cookies()
    driver.get(homepage_url)
    title = driver.title
    if title == "ZEIT ONLINE | Lesen Sie zeit.de mit Werbung oder im PUR-Abo. Sie haben die Wahl.":
        try:
            WebDriverWait(driver, 20).until(EC.frame_to_be_available_and_switch_to_it(0))
            WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CLASS_NAME, class_name))).click()
            driver.switch_to.default_content()
            WebDriverWait(driver, 20).until(EC.title_is('ZEIT ONLINE | Nachrichten, News, Hintergründe und Debatten'))
            text = driver.page_source
            log.info("The consent button was successfully clicked.")
        except TimeoutException:
            text = "Element could not be found, connection timed out."
            log.error(f"{homepage_url}: {text}")
    elif title == "ZEIT ONLINE | Nachrichten, News, Hintergründe und Debatten":
        text = driver.page_source
        log.info("The consent button was already clicked.")
    else:
        current_url = driver.current_url
        message = f"Please check that you are on the correct page. The current URL is {current_url} and the title is '{title}'."
        log.error(message)
        text = None
    return text, driver

'''@cli.command(help='Presses the consent button on the homepage of a website with a so-called "Pur Abo".')
@click.option('-u','--homepage-url',
              help='This is the URL you extract the article URLs from. When using the BeautifulSoup pipeline, this can also be  HTML source code.')
@click.option('-c', '--class-name', default='sp_choice_type_11',
              help='This is the class name of the consent button. If no name is given, '
              'newsfeedback uses the class name used by ZEIT Online for their consent button.')
def consent_button_homepage(homepage_url, class_name):
    accept_pur_abo_homepage(homepage_url, class_name)'''

def accept_pur_abo_article(article_url_list, class_name):
    options = webdriver.ChromeOptions()
    options.add_argument('headless') # comment out if you want to see what's happening
    options.add_argument('--log-level=3')
    options.add_argument('--lang=en')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    driver.delete_all_cookies()
    driver.refresh()
    if len(article_url_list) != 0:
        driver.get(article_url_list[0])
    else:
        homepage_url = "https://www.zeit.de/"
        driver.get(homepage_url)
    title = driver.title
    if title == "ZEIT ONLINE | Lesen Sie zeit.de mit Werbung oder im PUR-Abo. Sie haben die Wahl.":
        try:
            WebDriverWait(driver, 20).until(EC.frame_to_be_available_and_switch_to_it(0))
            driver.implicitly_wait(10)
            WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CLASS_NAME, class_name))).click()
            driver.switch_to.default_content()
            # WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body[data-page-type="article"]')))
            WebDriverWait(driver, 30).until(EC.any_of(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'body[data-page-type="article"]')),
                EC.none_of(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "title='ZEIT ONLINE | Lesen Sie zeit.de mit Werbung oder im PUR-Abo. Sie haben die Wahl.'"))
                    )
                    ))
            text = driver.page_source
            log.info("The consent button was successfully clicked.")
        except TimeoutException:
            text = 'Element could not be found, connection timed out.' 
            log.error(f"{article_url_list[0]}: {text}")
    else:
        text = driver.page_source
        log.info("The consent button was already clicked.")
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
    except:
        log.error('Unexpected error occured.')
    driver.quit()
    return article_url_list

def get_pur_abo_article_metadata_chain(homepage_url, driver, article_url_list):
    article_list = []
    metadata_config = retrieve_config("metadata")
    metadata_wanted = [k for k,v in metadata_config.items() if v == True]
    metadata_wanted.append('datetime')
    for article_url in article_url_list:
        if article_url != None:
            WebDriverWait(driver, 30).until(EC.any_of(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'body[data-page-type="article"]')),
                EC.none_of(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "title='ZEIT ONLINE | Lesen Sie zeit.de mit Werbung oder im PUR-Abo. Sie haben die Wahl.'"))
                    )
                    ))
            for x in range(5,20):
                try:
                    driver.get(article_url)
                except TimeoutException:
                    log.info(f"TimeoutException occurred, retrying after {x ** 2} seconds.")
                    driver.implicitly_wait(x ** 2)
                    driver.get(article_url)
                    if x == 20 and driver.page_source == None:
                        log.error("TimeoutException occurred and could not be resolved.")
                        ### send mail here
                        continue
                if driver.page_source != None:
                    break
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
                else:
                    metadata = {}
            else:  
                metadata = {}
            if len(metadata) != 0: # nested a bit too deep for my tastes, will refactor eventually
                for k,v in metadata.items():
                    if k == 'text':
                        v_new = v.replace('"',"“").replace("'","’").replace("\n","[¶]") # will this cause issues with URLs later? maybe!
                        v = f'"{v_new}"'
                        k_v_new ={k:v}
                        metadata.update(k_v_new)
                    elif k == 'comments':
                        v_new = v.replace('"',"“").replace("'","’").replace("\n","[¶]") # will this cause issues with URLs later? maybe!
                        v = f'"{v_new}"'
                        k_v_new ={k:v}
                        metadata.update(k_v_new)
                    else:
                        pass
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
    ### later this url blacklist will be modular, same with the regex parameters
    url_specific_blacklist = ['https://www.zeit.de/exklusive-zeit-artikel']
    year = time.strftime(r"%Y")
    regex_parameters = fr"((/(\w+-)+\w+-\w+(\.html)?)|/-/\w+|{year})" # adjust regex so that /index end is kicked
    if filter_choice == 'on':
        filtered_url_list = []
        for article in article_url_list:
            viable_article = re.search(regex_parameters, article) 
            if viable_article and article not in url_specific_blacklist:
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
    Path(output_folder).mkdir(exist_ok=True)
    output_subfolder = Path(output_folder/df_name)
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

'''@cli.command(help="[TRAFILATURA PIPELINE] - Executes the complete trafilatura pipeline.")
@click.option('-u','--homepage-url',
              help='This is the URL you extract the article URLs from.')
@click.option('-f', '--filter-choice',
              help="Whether you want to filter results or not. Either 'on' or 'off'.")
@click.option('-o', '--output-folder', default='newsfeedback/output',
              help="Defaults to newsfeedback's output folder.")
def trafilatura_pipeline(homepage_url, filter_choice, output_folder):
    chained_trafilatura_pipeline(homepage_url, filter_choice, output_folder)'''

def chained_beautifulsoup_pipeline(homepage_url, filter_choice, output_folder):
    article_url_list = get_article_urls_bs_pipeline(homepage_url)
    filtered_url_list = filter_urls(article_url_list, filter_choice)
    df = get_article_metadata_chain_bs_pipeline(filtered_url_list)
    df_path = export_dataframe(df, homepage_url, output_folder)
                  
    return df_path

'''@cli.command(help="[BEAUTIFULSOUP PIPELINE] - Executes the complete beautifulsoup pipeline.")
@click.option('-u','--homepage-url',
              help='This is the URL you extract the article URLs from.')
@click.option('-f', '--filter-choice',
              help="Whether you want to filter results or not. Either 'on' or 'off'.")
@click.option('-o', '--output-folder', default='newsfeedback/output',
              help="Defaults to newsfeedback's output folder.")
def beautifulsoup_pipeline(homepage_url, filter_choice, output_folder):
    chained_beautifulsoup_pipeline(homepage_url, filter_choice, output_folder)'''

def chained_purabo_pipeline(homepage_url, class_name, filter_choice, output_folder):
    (text, driver) = accept_pur_abo_homepage(homepage_url, class_name)
    article_url_list = get_pur_abo_article_urls_chain(text, driver)
    if len(article_url_list) < 2:
        for x in range(5,20):
            driver.quit()
            log.info(f"Retrying in {x ** 2} seconds.")
            time.sleep(x ** 2)
            (text, driver) = accept_pur_abo_homepage(homepage_url, class_name)
            article_url_list = get_pur_abo_article_urls_chain(text, driver)
            if x == 20 and len(article_url_list) == 0:
                log.error(f"{homepage_url}: Due to an error accepting the first pur abo button, no articles with metadata were found, despite sufficient wait.")
            if len(article_url_list) != 0:
                break
    returned_article_url_list = filter_urls(article_url_list, filter_choice)
    driver.quit()
    (text, driver) = accept_pur_abo_article(returned_article_url_list, class_name)
    df = get_pur_abo_article_metadata_chain(homepage_url, driver, returned_article_url_list)
    if df.shape[0] <= 2:
        for x in range(5,20):
            driver.quit()
            log.info(f"Retrying in {x ** 2} seconds.")
            time.sleep(x ** 2)
            (text, driver) = accept_pur_abo_article(returned_article_url_list, class_name)
            df = get_pur_abo_article_metadata_chain(homepage_url, driver, returned_article_url_list)
            if x == 20 and df.shape[0] == 0:
                driver.quit()
                log.error(f"{homepage_url}: Due to an error accepting the second pur abo button, no articles with metadata were found, despite sufficient wait.")
            if df.shape[0] != 0:
                driver.quit()
                break
    else:
        driver.quit()
    export_dataframe(df, homepage_url, output_folder)
'''
@cli.command(help="[PURABO PIPELINE] - Executes the complete pur abo pipeline.")
@click.option('-u','--homepage-url',
              help='This is the URL you extract the article URLs from.')
@click.option('-c', '--class-name', default='sp_choice_type_11',
              help='This is the class name of the consent button. If no name is given, '
              'newsfeedback uses the class name used by ZEIT Online for their consent button.')
@click.option('-f', '--filter-choice',
              help="Whether you want to filter results or not. Either 'on' or 'off'.")
@click.option('-o', '--output-folder', default='newsfeedback/output',
              help="Defaults to newsfeedback's output folder.")
def purabo_pipeline(homepage_url, class_name, filter_choice, output_folder):
    chained_purabo_pipeline(homepage_url, class_name, filter_choice, output_folder)'''

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
        log.error(f"Please check that the URL you have given ({homepage_url}) matches the required structure (https://www.name.de/) "
                  "and has already been added to the config. Otherwise add it to the config via the CLI "
                  "with 'newsfeedback add-homepage-url'. Data may be coming from an unintended config (default/custom). ")
    
@cli.command(help="Chooses and executes the pipeline saved in the config file.")
@click.option('-u','--homepage-url',
              help='This is the URL you extract the article URLs from.')
@click.option('-o', '--output-folder', default='newsfeedback/output',
              help="Defaults to newsfeedback's output folder.")

def pipeline_picker(homepage_url, output_folder):
    get_pipeline_from_config(homepage_url, output_folder)

def copy_default_to_metadata_config(answer, tmp_path=False):
    if answer != "Y" and answer != "testing_tmp_path":
        pass
    else:
        if answer == 'Y':
            directory = Path().resolve()
            path_user_metadata_config = directory/"user_metadata_config.yaml"
            path_default_metadata_config = directory/"newsfeedback"/"defaults"/"default_metadata_config.yaml"
        else:
            tmp_directory = Path(tmp_path)
            directory = Path().resolve()
            path_user_metadata_config = tmp_directory/"tmp_user_metadata_config.yaml"
            path_default_metadata_config = directory/"newsfeedback"/"defaults"/"default_metadata_config.yaml"

        if Path(path_user_metadata_config).exists():
            log.error(f'You have already generated a user config file at {path_user_metadata_config}. '
                    'Please update the settings manually within the file.')
        else:               
            path_user_metadata_config.write_bytes(path_default_metadata_config.read_bytes())
            try:
                with open(path_user_metadata_config, 'a+') as yamlfile:
                    data = yaml.safe_load(yamlfile)     
                    log.info(f"Successfully created a user config with the default metadata. Please adjust "
                             f"settings manually at {path_user_metadata_config}, if so desired.")
            except:
                log.error('There was an unexpected error.')

def copy_default_to_homepage_config(answer, tmp_path=False):
    if answer != "Y" and answer != "testing_tmp_path":
        pass
    else:
        if answer == 'Y' or answer == 'y':
            directory = Path().resolve()
            path_user_homepage_config = directory/"user_homepage_config.yaml"
            path_default_homepage_config = directory/"newsfeedback"/"defaults"/"default_homepage_config.yaml"
        else:
            tmp_directory = Path(tmp_path)
            directory = Path().resolve()
            path_user_homepage_config = tmp_directory/"tmp_user_homepage_config.yaml"
            path_default_homepage_config = directory/"newsfeedback"/"defaults"/"default_homepage_config.yaml"
            
        if Path(path_user_homepage_config).exists():
            default_data = retrieve_config("homepage_default")
            default_homepages = list(default_data.keys())
            user_data = retrieve_config("homepage") # as the path exists, this will grab the user config file
            user_homepages = list(user_data.keys())
            new_homepages = [k for k in default_homepages if k not in user_homepages]

            for homepage_url in new_homepages:
                data = default_data.get(homepage_url) # {'pipeline': '...', 'filter': '...'}
                new_homepage = {homepage_url: data} # {homepage_url: {'pipeline': '...', 'filter': '...'}}
                with open(path_user_homepage_config, 'a+') as yamlfile:
                    yaml.dump(new_homepage, yamlfile)

            updated_data = retrieve_config("homepage")
            updated_homepages = list(updated_data.keys())
            log.info(f"Successfully appended {len(new_homepages)} homepage(s) to the user config, which now holds the "
                     f"following URLs: {updated_homepages}")
        else:
            path_user_homepage_config.write_bytes(path_default_homepage_config.read_bytes())
            log.info(path_user_homepage_config)
            with open(path_user_homepage_config, 'a+') as yamlfile:
                data = yaml.safe_load(yamlfile)            
                log.info(f"Successfully created a user config with the default homepages.")

@cli.command(help="Generates a new metadata or homepage config to allow custom settings.")
@click.option('-c', '--choice',
              help='Prompts the user to choose a type of config to generate.',
              prompt='[1/2] Choose the type of config you wish to generate '
              '1. metadata OR 2. homepage '              )
@click.option('-a', '--answer',
              help='[2/2] Confirmation (or rejection) of custom file generation.',
              prompt="Do you want to generate this new config? Y|N")

def generate_config(choice, answer):
    if answer == "Y" or answer == "y":
        if choice == '1' or choice == 'metadata':
            copy_default_to_metadata_config(answer)
        elif choice == '2' or choice == 'homepage':
            copy_default_to_homepage_config(answer)
        else:
            log.error('Please enter a viable answer (i.e. "1", "2", "metadata" or "homepage").')
    else:
        pass

def write_in_homepage_config(homepage_url, chosen_pipeline, filter_option, tmp_path=False):
    if tmp_path:
        tmp_path = Path(tmp_path)
        path_tmp_user_homepage_config = tmp_path/"tmp_user_homepage_config.yaml"
        log.info(f"Generating a new entry at {path_tmp_user_homepage_config}")
        new_homepage = {
            homepage_url: {
                'pipeline': chosen_pipeline,
                'filter' : filter_option.replace("'","")
            }
        }

        with open(path_tmp_user_homepage_config, 'a+') as yamlfile:
            yaml.dump(new_homepage, yamlfile)

        log.info(f"{new_homepage} has been added to {path_tmp_user_homepage_config}.")
    else:
        directory = Path().resolve()
        path_user_homepage_config = directory/"user_homepage_config.yaml"

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
        with open(path_user_homepage_config, 'a+') as yamlfile:
            yaml.dump(new_homepage, yamlfile)

        log.info(f"{new_homepage} has been added to {path_user_homepage_config}.")      


@cli.command(help="Adds a new homepage to the config file.")
@click.option('-u', '--homepage-url',
              prompt="Your homepage URL (required format: https://www.name.de/) ",
              help="The homepage URL you wish to add (i.e. https://www.spiegel.de/) to the config file. "
              "Please follow the example URL structure to reduce the potential for duplicates. ")
@click.option('-p', '--chosen-pipeline',
              prompt="[1/2] Pick one of the available pipelines: 1 - trafilatura, 2 - beautifulsoup, 3 - purabo ",
              help="The pipeline through which your article URLs and metadata are extracted. They are named for "
              "the packages and libraries primarily used in extraction. \n [trafilatura] has a higher error rate but "
              "no need for extra filtering. [beautifulsoup] works for all webpages, but requires further filtering. "
              "If a website has a so-called Pur Abo (i.e. ZEIT online), the [purabo] is the only viable option.")
@click.option('-f', '--filter-option',
              prompt="[2/2] Decide if you want filtering. Type 'on' or 'off'",
              help="Filtering is recommended for the beautifulsoup and purabo pipelines, "
              "but not for the trafilatura pipelines. It roughly filters out nonviable URLs "
              "retrieved in broader extraction processes.")
def add_homepage_url(homepage_url, chosen_pipeline, filter_option):
    write_in_homepage_config(homepage_url, chosen_pipeline, filter_option)

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
              help="Defaults to newsfeedback's output folder.")
def get_data(hour, output_folder):
    initiate_data_collection(output_folder)
    schedule.every(int(hour)).hours.do(initiate_data_collection, output_folder)
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "main":
    cli()