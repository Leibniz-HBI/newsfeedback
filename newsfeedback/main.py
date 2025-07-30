import trafilatura, click, re, time, yaml, os, schedule, requests, random, decimal, warnings
import pandas as pd
from pathlib import Path
from trafilatura import feeds
from loguru import logger as log
from bs4 import BeautifulSoup
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException,WebDriverException
from urllib3.exceptions import ReadTimeoutError, HTTPError
from sqlalchemy import create_engine, inspect
from nltk.tokenize import RegexpTokenizer



@click.group()
def cli():
    pass

def sql_engine(): # database info
    user = ""
    pw = ""
    db = ""
    host = ""
    port = ""
    uri = f"postgresql+psycopg2://{user}:{pw}@{host}:{port}/{db}"
    alchemyEngine = create_engine(uri)  
    return alchemyEngine

def retrieve_config(type_config, tmp_path=False):
    directory = Path().resolve()
    path_user_metadata_config = directory/"user_metadata_config.yaml"
    path_default_metadata_config = directory/"newsfeedback"/"defaults"/"default_metadata_config.yaml"
    path_user_homepage_config = directory/"user_homepage_config.yaml"
    path_default_homepage_config = directory/"newsfeedback"/"defaults"/"default_homepage_config.yaml"
    path_user_filter_choice_config = directory/"user_filter_choice_config.yaml"
    path_default_filter_choice_config = directory/"newsfeedback"/"defaults"/"default_filter_choice_config.yaml"
    path_default_filter_sections_config = directory/"newsfeedback"/"defaults"/"default_filter_sections_config.yaml"
    if tmp_path:
        path_tmp_metadata_config = tmp_path/"tmp_metadata_config.yaml"
        path_tmp_homepage_config = tmp_path/"tmp_homepage_config.yaml"
        path_tmp_filter_choice_config = tmp_path/"tmp_filter_choice_config.yaml"
        path_tmp_filter_sections_config = tmp_path/"tmp_filter_sections_config.yaml"

    if type_config == "metadata":
        if Path(path_user_metadata_config).exists():
            config_file = Path(path_user_metadata_config)
            #log.info(f"Using the user-generated {type_config} config at {config_file}.")
        else:
            config_file = Path(path_default_metadata_config)
            #log.info(f"Using the default {type_config} config at {config_file}.")
    elif type_config == "metadata_default":
        config_file = Path(path_default_metadata_config)
        #log.info(f"Using the default {type_config} config at {config_file}.")
    elif type_config == "metadata_test":
        config_file = Path(path_tmp_metadata_config)
        config_file.write_bytes(path_default_metadata_config.read_bytes())
        #log.info(f"Using the default {type_config} config at {config_file}.")

    elif type_config == "homepage":
        if Path(path_user_homepage_config).exists():
            config_file = Path(path_user_homepage_config)
            # log.info(f"Using the user-generated {type_config} config at {config_file}.")
        else:
            config_file = Path(path_default_homepage_config)
            # log.info(f"Using the default {type_config} config at {config_file}.")
    elif type_config == "homepage_default":
        config_file = Path(path_default_homepage_config)
        #log.info(f"Using the default {type_config} config at {config_file}.")
    elif type_config == "homepage_test":
        config_file = Path(path_tmp_homepage_config)
        config_file.write_bytes(path_default_homepage_config.read_bytes())
        #log.info(f"Using the default {type_config} config at {config_file}.")
  
    elif type_config == "filter_choice":
        if Path(path_user_filter_choice_config).exists():
            config_file = Path(path_user_filter_choice_config)
            #log.info(f"Using the user-generated {type_config} config at {config_file}.")
        else:
            config_file = Path(path_default_filter_choice_config)
            #log.info(f"Using the default {type_config} config at {config_file}.")
    elif type_config == "filter_choice_default":
        config_file = Path(path_default_filter_choice_config)
        #log.info(f"Using the default {type_config} config at {config_file}.")
    elif type_config == "filter_choice_test":
        config_file = Path(path_tmp_filter_choice_config)
        config_file.write_bytes(path_default_filter_choice_config.read_bytes())
        #log.info(f"Using the default {type_config} config at {config_file}.")

    elif type_config == "filter_sections":
        config_file = Path(path_default_filter_sections_config)
        #log.info(f"Using the default {type_config} config at {config_file}.")
    elif type_config == "filter_Sections_test":
        config_file = Path(path_tmp_filter_sections_config)
        config_file.write_bytes(path_default_filter_sections_config.read_bytes())
        #log.info(f"Using the default {type_config} config at {config_file}.")

    with config_file.open() as yamlfile:
        data = yaml.load(yamlfile, Loader=yaml.FullLoader)
        return data


def click_popup(driver):
    try:
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//div[contains(@id, 'sp_message_container_')]")))
        find_container = driver.find_element(By.XPATH, "//iframe[contains(@id, 'sp_message_iframe_')]")
        driver.switch_to.frame(find_container)
        find_button = driver.find_element(By.XPATH, "//button[contains(@class, 'sp_choice_type_11')]")
        find_button.click()
        driver.implicitly_wait(5)
        WebDriverWait(driver, 20).until(EC.none_of(EC.presence_of_element_located((By.CLASS_NAME, "message-overlay"))))
        log.info("TCF consent button was successfully clicked.")
    except TimeoutException:
        log.info("TCF consent button could not be found, trying again.")
        try:
            find_button = driver.find_element(By.XPATH, "//button[contains(@class, 'sp_choice_type_11')]")
            find_button.click()
            driver.implicitly_wait(5)
            WebDriverWait(driver, 20).until(EC.none_of(EC.presence_of_element_located((By.CLASS_NAME, "message-overlay"))))
            log.info("TCF consent button was successfully clicked.")
        except TimeoutException:
            log.info("TCF consent button could not be found, connection timed out.") 
        except NoSuchElementException:
            log.info("TCF could not be found. Continuing.")   
    except NoSuchElementException:
        log.info("TCF could not be found. Continuing.")
    return driver


def duplicate_article_checker(homepage_url, article_url_list): # check if url is already in database or has been filtered out
    warnings.simplefilter(action='ignore', category=UserWarning)
    db_name = '' ## database info
    homepage_url_selected = re.search(r"(www\.)?(\w|-|_)*?\.\w{2,5}(\.\w{2,})?\/", homepage_url)
    homepage_url = homepage_url_selected.group(0)
    hostname = homepage_url.replace('www.', '')
    hostname = hostname.replace('/','')
    user = ""
    pw = ""
    db = ""
    host = ""
    port = ""
    uri = f"postgresql+psycopg2://{user}:{pw}@{host}:{port}/{db}"
    alchemyEngine = create_engine(uri) 
    with alchemyEngine.connect() as conn:
        df = pd.read_sql(f"SELECT * FROM {db_name} WHERE hostname = '{hostname}'", con=conn.connection)
    kick_list = list(dict.fromkeys(df['url'].values.tolist()))
    with open("/data_collection/newsfeedback/default_article_blacklist.txt", "r+") as f:
        for line in f:
            kick_list.append(line.rstrip('\n'))

    kick_list.append(homepage_url)
    kick_list.append(homepage_url.replace('www.',''))
    kick_list.append(homepage_url[:-1])
    article_url_list_no_dups = list(dict.fromkeys(article_url_list))
    article_list_kicked_entries = [article for article in article_url_list_no_dups if article not in kick_list]

    return article_list_kicked_entries


def baseline_filter(df): # check if article is relevant based on structure

    warnings.simplefilter(action='ignore', category=UserWarning)
    re1 = r"((latest|breaking)(.*?) (news|headlines)(( and | & |, fixtures and )(updates|analysis))?)|(reviewed .*?latest deals)|(boxing news.+? latest|stock.*?latest stocks)"
    re2 = r"^\S*?( \S*?){,3} (\||-) (MIT .*? Review|The Independent|The Boston Globe|The Economist|UK|US|World|Culture|Life & Style|Sport|Business & Money)$|Travel Guides . Telegraph Travel"
    re3 = r"^\S+$|^\S*?( \S*?){,2}$"
    re4 =  r"((aktuelle.*?(news|themen|nachrichten|beitr.ge|lage und hintergr.nde|berichte|hintergr.nde|umfrage|tv Programm))|aktuelles (f.r|zu)|^aktuell$|regenradar|d.rre-karte|deutschlandfunk aktuell|news:.*?aktuell)"
    re5 = r"Alle Tagesspiegel-Artikel vom (\d{2}\.){2}\d{4}"
    re6 = r"page not found|^Datenschutzerklärung|^Nutzungsbedingungen|Allgemeine Gesch.ftsbedingungen|Impressum|^Widerruf Nutzerkennungen|Teilnahmebedingungen|terms (and|&) conditions|^Contact Us$|^Letters to the Editor$|(Privacy|User).*?(Cookie)?.*?Polic(y|ies)|Cookie Notice|Code of Conduct|Modern Slavery Statement|editorial.*?guidelines"
    re7 = r"RTL\.de: Nachrichten, die Deutschland bewegen|Alle News, Geschichten und Highlights|Alles rund um wichtige Themen und Personen|Rechner, Lexika & Orakel: Kostenlose Online-Tools|die \d+ besten .*? im Vergleich"
    regex_pattern = fr"({re1}|{re2}|{re3}|{re4}|{re5}|{re6}|{re7})"
    filter_out_df = df[df['title'].str.contains(regex_pattern, na=False)]
    url_kick_list = filter_out_df['url'].values.tolist()
    final_url_kick_list = list(dict.fromkeys(url_kick_list))
    url_list = []
    with open("/data_collection/newsfeedback/default_article_blacklist.txt", "a+") as f:
        for line in f:
            url_list.append(line.rstrip('\n'))
        url_list = list(dict.fromkeys(url_list))
        for url in final_url_kick_list:
            if url not in url_list:
                f.write(f"{url}\n")
        f.close()
    remaining_df = df[~df['title'].str.contains(regex_pattern, na=False)]
    return remaining_df

### TRAFILATURA PIPELINE

def get_article_urls_trafilatura_pipeline(homepage_url):
    article_url_list = feeds.find_feed_urls(homepage_url)
    unique_article_url_list = duplicate_article_checker(homepage_url, article_url_list)
    if len(article_url_list) != 0:
        log.info(f'{homepage_url}: {len(unique_article_url_list)} articles were found. [{len(article_url_list)-len(unique_article_url_list)} of {len(article_url_list)} articles removed]\r')
        article_url_list = unique_article_url_list
    else:
        article_url_list = []
        log.error(f'{homepage_url}: {len(article_url_list)} articles were found.')
    return article_url_list



def get_article_metadata_chain_trafilatura_pipeline(article_url_list):
    metadata_config = retrieve_config("metadata")
    metadata_wanted = [k for k,v in metadata_config.items() if v == True]
    metadata_wanted.append('datetime_retrieved')
    article_list = []
    for article_url in tqdm(article_url_list, colour="white"):
        downloaded = trafilatura.fetch_url(article_url)
        try:
            metadata = trafilatura.bare_extraction(downloaded, only_with_metadata=True, include_links=True)
        except AttributeError:
            metadata = None
        if metadata is not None:
            if type(metadata) != dict:
                metadata = metadata.as_dict()
            dict_keys = list(metadata.keys())
            dict_keys_to_pop = [key for key in dict_keys if key not in metadata_wanted]
            if len(dict_keys_to_pop) != 0:
                for key in dict_keys_to_pop: 
                    metadata.pop(key, None)
            else:
                metadata = metadata
            datetime = time.strftime(r"%Y-%m-%d %H:%M:%S")
            pd_datetime = pd.to_datetime(datetime)
            datetime_column = {'datetime_retrieved':pd_datetime}
            metadata.update(datetime_column)
        else:
            metadata = []
        if len(metadata) != 0:
            for k,v in metadata.items():
                if k == 'text':
                    v_new = v.replace('"',"â€œ").replace("'","â€™").replace("\n","[Â¶]") # will this cause issues with URLs later? maybe!
                    v = f'"{v_new}"'
                    k_v_new ={k:v}
                    metadata.update(k_v_new)
                elif k == 'comments':
                    v_new = v.replace('"',"â€œ").replace("'","â€™").replace("\n","[Â¶]") # will this cause issues with URLs later? maybe!
                    v = f'"{v_new}"'
                    k_v_new ={k:v}
                    metadata.update(k_v_new)
                elif k == 'url':
                    if v != article_url:
                        k_v_new = {k:f"{article_url}"}
                        metadata.update(k_v_new)
                    if re.search(r"^https?:\/\/image-de\.",v):
                        k_v_new = {k:f"{v.replace('image-de','www')}"}
                        metadata.update(k_v_new)
                else:
                    pass     
            if "text" in metadata.keys():
                    text_value = metadata["text"]
                    tokenizer = RegexpTokenizer(r'\w+')
                    token_count = tokenizer.tokenize(text_value)
                    if "token_count" not in metadata_wanted or "character_count" not in metadata_wanted:
                        metadata_wanted.append("token_count")
                        metadata_wanted.append("character_count")
                    metadata.update({"token_count":len(token_count)})
                    metadata.update({"character_count":len(text_value)})
        article_list.append(metadata)
    try:
        df = pd.DataFrame(article_list, columns = metadata_wanted)
        df['date'] = pd.to_datetime(df['date'], format= r'%Y-%m-%d')
        df = df.rename(columns={'date':'date_published'})       
        filtered_df = baseline_filter(df)
        log.info(f'{filtered_df.shape[0]} articles with metadata were found. [{df.shape[0] - filtered_df.shape[0]} of {df.shape[0]} articles were removed]\r')
        df = filtered_df
    except ValueError or TypeError:
        df = pd.DataFrame(columns=metadata_wanted)
        df['date'] = pd.to_datetime(df['date'], format= r'%Y-%m-%d')
        df = df.rename(columns={'date':'date_published'})
        log.error('No articles with metadata were found.')
    return df

### BEAUTIFULSOUP PIPELINE

def get_article_urls_bs_pipeline(homepage):
    article_url_list = []
    if len(homepage) < 80:
        sites_blocked_trafilatura = ["https://www.spiegel.de/"]
        sites_requiring_javascript = ["https://www.handelsblatt.com/", "https://www.derstandard.at/", "https://www.wiwo.de/", "https://www.politico.com/"]
        if homepage not in sites_blocked_trafilatura and homepage not in sites_requiring_javascript:
            downloaded = trafilatura.fetch_url(homepage)
        else:
            headers = {'user-agent':'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.7049.38 Mobile Safari/537.36'}
            try:
                r = requests.get(homepage, timeout=5, headers=headers)
            

                if r.status_code == requests.codes.ok:                
                    downloaded = r.text
                    r.close()
                    time.sleep(float(decimal.Decimal(random.randrange(100, 400))/100))
                else:
                    r.raise_for_status()
                    downloaded = ""
            except TimeoutError:
                log.warning("Request timed out.")
                downloaded = ""
            except HTTPError:
                log.warning(f"{HTTPError}")
                downloaded = ""
            javascript_search = re.search('enable JavaScript', downloaded)
            if homepage in sites_requiring_javascript or javascript_search:
                log.info(f"{homepage}: turning on JavaScript.")
                options = webdriver.ChromeOptions()
                options.add_argument('--headless=new') # comment out if you want to see what's happening
                options.add_argument('--log-level=3')
                #options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                #options.add_argument('--lang=en')
                options.add_argument('--user-agent=Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.7049.38 Mobile Safari/537.36')

                # options.add_argument('--lang=en')
                #options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0')
                options.add_experimental_option('excludeSwitches', ['enable-logging'])
                options.add_argument('--enable-javascript')    
                
                driver = webdriver.Chrome(options=options)
                driver.command_executor.set_timeout(1000)
                driver.get(homepage)
                time.sleep(float(decimal.Decimal(random.randrange(100, 400))/100)) # randomize float 
                try:
                    old_driver = driver
                    driver = click_popup(old_driver)
                except ReadTimeoutError as e:
                    log.warning(f"Popup clicker timed out.")
                time.sleep(float(decimal.Decimal(random.randrange(100, 400))/100)) # randomize float 
                downloaded = driver.page_source
                driver.quit()
        homepage_url = homepage
    else:
        downloaded = homepage
    try:
        soup = BeautifulSoup(downloaded, 'html.parser')
    except TypeError as e:
        log.info(f"{homepage}: trying again with Selenium.")
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new') # comment out if you want to see what's happening
        options.add_argument('--log-level=3')
        #options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        # options.add_argument('--lang=en')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        driver = webdriver.Chrome(options=options)
        driver.command_executor.set_timeout(1000)
        try:
            driver.get(homepage)
            time.sleep(float(decimal.Decimal(random.randrange(100, 400))/100)) # randomize float 
            downloaded = driver.page_source
            '''directory = Path().resolve()
            with open("web_test.txt", "w+") as text_file:
                text_file.write(downloaded)
                text_file.close()'''
            driver.quit()
            soup = BeautifulSoup(downloaded, 'html.parser')
        except TimeoutError:
            log.warning(f"{homepage} timed out. Continuing to next URL.")
            downloaded = ""
        except TypeError as e:
            log.warning(f"{homepage} error: {e}. Continuing to next URL.")
            downloaded = ""
        except requests.ReadTimeout or ReadTimeoutError:
            log.warning(f"{homepage} read timed out. Continuing to next URL.")
            downloaded = ""
        except WebDriverException as e: 
            log.error(f"{homepage} error: {e}. Continuing to next URL.")
            downloaded = ""
        soup = BeautifulSoup(downloaded, 'html.parser')
    for a in soup.find_all('a'):
        href = a.get('href')
        fix_ww = re.search(r'https?:\/\/ww\..+', f"{href}")
        if fix_ww:
            href_new = str(href).replace('//ww.', '//www.')
            href = href_new
        various_check = re.search(r"mailto\:|#", f'{href}')

        if various_check != None:
            continue
        backslash_check = re.search(r'https?:\/{2}.*\.\w{2,3}\/$', f'{href}')
        
        if backslash_check != None:
            continue

        http_check = re.search(r'http', f'{href}')

        if href != None:

            if http_check == None:

                http_url = f"{homepage_url}" + f"{href}"
                double_slash_check = re.search(r"(?<!https:)(//)", http_url)
                if double_slash_check:
                    http_url = re.sub(r"(?<!https:)(//)", r"/", http_url)
                double_de_check = re.search(r"/de/de/", http_url)
                if double_de_check:
                    http_url = re.sub(r"/de/de/", r"/de/", http_url)
                double_url_check = re.search(r"(\/{2}www\..*?){2}", http_url)
                if double_url_check:
                    http_url = re.sub(r"\/{2}.*?\/{2}", "//", http_url)
                article_url_list.append(http_url)
                

            else:
                
                homepage_de = re.search(r'(https?:\/\/(www\.)?.+?\.\w{2,3}/de/)', homepage_url)
                if homepage_de:
                    homepage_split = homepage_de.group(0)
                else:
                    homepage_split = re.search(r'(https?:\/\/(www\.)?.+?\.\w{2,3})', homepage_url).group(0) # get host name out of url -> adjust to allow web.host, tech.host, etc?
                
                      
                homepage_check = re.search(fr'{homepage_split}\/.+', href) 
                if homepage_check:
                    article_url_list.append(href)
                else:

                    homepage_url_no_www = homepage_url.replace('https://www.','')

                    homepage_check = re.search(fr'{homepage_url_no_www.lower()}.+', href)
                    if homepage_check:
                        article_url_list.append(href)
    article_url_list_to_clean = article_url_list
    article_url_list_no_dupes = list(dict.fromkeys(article_url_list_to_clean)) # refactor these!
    article_url_list_no_none = list(filter(lambda item: item is not None, article_url_list_no_dupes))
    unique_article_url_list = duplicate_article_checker(homepage_url, article_url_list_no_none)
    if len(unique_article_url_list) != 0:
        log.info(f'{homepage_url}: {len(unique_article_url_list)} articles were found. [{len(article_url_list)-len(unique_article_url_list)} of {len(article_url_list)} articles removed]\r')
        article_url_list = unique_article_url_list
    else:
        try:
            log.info(f'{homepage_url}: {len(article_url_list)} articles were found. [{len(article_url_list)-len(unique_article_url_list)} of {len(article_url_list)} articles removed]\r')
        except TypeError as e:
            article_url_list = []
            log.error(f'{homepage_url}: {len(article_url_list)} articles were found. [{len(article_url_list)-len(unique_article_url_list)} of {len(article_url_list)} articles removed]\r')
    return article_url_list


def get_article_metadata_chain_bs_pipeline(article_url_list):
    metadata_config = retrieve_config("metadata")
    metadata_wanted = [k for k,v in metadata_config.items() if v == True]
    article_list = []
    metadata_wanted.append('datetime_retrieved')
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new') # comment out if you want to see what's happening
    options.add_argument('--log-level=3')
    #options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    #options.add_argument('--lang=en')
    #options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0')
    options.add_argument('--user-agent=Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.7049.38 Mobile Safari/537.36')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_argument('--enable-javascript')      
    driver = webdriver.Chrome(options=options)
    driver.command_executor.set_timeout(1000)
        

    for article in tqdm(article_url_list, colour="white"):
        if len(article) < 300:
            sites_blocked_trafilatura = ["https://www.spiegel.de/"]
            sites_requiring_javascript = ["https://www.handelsblatt.com/", "https://www.derstandard.at/", "https://www.wiwo.de/", "https://www.politico.com/"]
            try:
                homepage_finder = re.match( r".*?\/\/(www\.)?.*?\.\w{2,5}\/?", article)
                homepage_found = homepage_finder.group()
            except AttributeError:
                log.warning(f"Error at: {article}")
                continue
            if homepage_found not in sites_blocked_trafilatura and homepage_found not in sites_requiring_javascript:
                downloaded = trafilatura.fetch_url(article)
                if downloaded == None:
                    downloaded = ""
                if downloaded == None or len(downloaded) < 1:
                    try:    
                        driver.get(article) 
                        if article == article_url_list[0]:
                            old_driver = driver
                            driver = click_popup(old_driver)
                            driver = old_driver
                        time.sleep(float(decimal.Decimal(random.randrange(100, 400))/100)) # randomize float                
                        downloaded = driver.page_source
                    except TimeoutError or socket.timeout:
                        log.warning(f"{article} timed out. Continuing to next URL.")
                        downloaded = ""
                    except requests.ReadTimeout or ReadTimeoutError:
                        log.warning(f"{article} read timed out. Continuing to next URL.")
                        downloaded = ""
                    except WebDriverException:
                        log.warning(f"{article} encountered a web driver exception. Continuing to next URL.")
            else:
                try:
                    r = requests.get(article, timeout=5)
                    if r.status_code == requests.codes.ok:                
                        downloaded = r.text
                        r.close()
                        time.sleep(float(decimal.Decimal(random.randrange(100, 400))/100)) # randomize float
                    else:
                        r.raise_for_status()
                        downloaded = ""
                except TimeoutError or socket.timeout:
                    log.warning(f"{article} timed out. Continuing to next URL.")
                    downloaded = ""
                except requests.ReadTimeout or ReadTimeoutError:

                    log.warning(f"{article} read timed out. Continuing to next URL.")
                    downloaded = ""
                if downloaded == None:
                    try:
                        driver.get(article) 
                        if article == article_url_list[0]:
                            old_driver = driver
                            driver = click_popup(old_driver)
                            driver = old_driver
                        time.sleep(float(decimal.Decimal(random.randrange(100, 400))/100)) # randomize float                
                        downloaded = driver.page_source
                    except TimeoutError or socket.timeout:
                        log.warning(f"{article} timed out. Continuing to next URL.")
                        downloaded = ""
                    except requests.ReadTimeout or ReadTimeoutError:
                        log.warning(f"{article} read timed out. Continuing to next URL.")
                        downloaded = ""

                else: # Handelsblatt, Der Standard
                    try:
                        driver.get(article) 
                        if article == article_url_list[0]:
                            old_driver = driver
                            driver = click_popup(old_driver)
                            driver = old_driver
                        time.sleep(float(decimal.Decimal(random.randrange(100, 400))/100)) # randomize float                
                        downloaded = driver.page_source
                    except TimeoutError or socket.timeout:
                        log.warning(f"{article} timed out. Continuing to next URL.")
                        downloaded = ""
                    except requests.ReadTimeout or ReadTimeoutError:
                        log.warning(f"{article} read timed out. Continuing to next URL.")
                        downloaded = ""
                    
        else:
            downloaded = article
        
        if downloaded != None:
            javascript_search = re.match('enable Javascript', downloaded)
            if javascript_search:
                options = webdriver.ChromeOptions()
                options.add_argument('headless=new') # comment out if you want to see what's happening
                options.add_argument('--log-level=3')
                options.add_argument("--enable-javascript")              
                #options.add_argument('--lang=en')
                #options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--user-agent=Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.7049.38 Mobile Safari/537.36')
                #options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0')
                options.add_experimental_option('excludeSwitches', ['enable-logging'])
                driver = webdriver.Chrome(options=options)
                driver.command_executor.set_timeout(1000)
                try:
                    driver.get(article)
                    downloaded = driver.page_source
                except TimeoutError or socket.timeout:
                    log.warning(f"{article} timed out. Continuing to next URL.")
                    
                except requests.ReadTimeout or ReadTimeoutError:
                    log.warning(f"{article} timed out. Continuing to next URL.")
            try:
                metadata = trafilatura.bare_extraction(downloaded, only_with_metadata=True, include_links=False, include_comments=True)
            except AttributeError:
                metadata = None
            if metadata != None:
                if type(metadata) != dict:
                    metadata = metadata.as_dict()
                dict_keys = list(metadata.keys())
                dict_keys_to_pop = [key for key in dict_keys if key not in metadata_wanted]
                if len(dict_keys_to_pop) != 0:
                    for key in dict_keys_to_pop: 
                        metadata.pop(key, None)
                else:
                    metadata = metadata
                datetime = time.strftime(r"%Y-%m-%d %H:%M:%S")
                pd_datetime = pd.to_datetime(datetime)
                datetime_column = {'datetime_retrieved':pd_datetime}
                metadata.update(datetime_column)
            else:
                metadata = {}
        else:  
            metadata = {}
        if len(metadata) != 0:

            for k,v in metadata.items():
                if k == 'text':
                    v_new = v.replace('"',"â€œ").replace("'","â€™").replace("\n","[¶]") # will this cause issues with URLs later? maybe!
                    if len(v_new) >= 10000:
                        v_truncated = v_new[:10000]
                        v_new = v_truncated
                    v = f'"{v_new}"'
                    k_v_new ={k:v}
                    metadata.update(k_v_new)
                    
                elif k == 'comments':
                    v_new = v.replace('"',"â€œ").replace("'","â€™").replace("\n","[]") # will this cause issues with URLs later? maybe!
                    v = f'"{v_new}"'
                    k_v_new ={k:v}
                    metadata.update(k_v_new)
                elif k == 'url':
                    if v != article:
                        k_v_new = {k:f"{article}"}
                        metadata.update(k_v_new)
                    if re.search(r"^https?:\/\/image-de\.",v):
                        k_v_new = {k:f"{v.replace('image-de','www')}"}
                        metadata.update(k_v_new)
                else:
                    pass
            if "text" in metadata.keys():
                text_value = metadata["text"]
                if len(text_value) >= 10000:
                    text_value = text_value[:10000]
                tokenizer = RegexpTokenizer(r'\w+')
                token_count = tokenizer.tokenize(text_value)
                if "token_count" not in metadata_wanted or "character_count" not in metadata_wanted:
                    metadata_wanted.append("token_count")
                    metadata_wanted.append("character_count")
                metadata.update({"token_count":f"{len(token_count)}"})
                metadata.update({"character_count":f"{len(text_value)}"})
            article_list.append(metadata)
    df = pd.DataFrame(article_list, columns = metadata_wanted)
    df['date'] = pd.to_datetime(df['date'], format= r'%Y-%m-%d')
    df = df.rename(columns={'date':'date_published'})
    if df.shape[0] != 0:
        filtered_df = baseline_filter(df)
        log.info(f'{filtered_df.shape[0]} articles with metadata were found. [{df.shape[0] - filtered_df.shape[0]} of {df.shape[0]} articles were removed]\r')
        df = filtered_df
    else:
        log.error(f'{df.shape[0]} articles with metadata were found.')
    driver.quit()
    return df


### Filter-related functions

def filter_urls(article_url_list, filter_choice):
                     
    if filter_choice == 'on': 
        filter_config = retrieve_config('filter_choice')
        filter_sections = retrieve_config('filter_sections')
        filter_wanted = [k for k,v in filter_config.items() if v == 'on']
        filter_sections_wanted = [str(v) for k,v in filter_sections.items() if k in filter_wanted]
        filter_sections_wanted_clean = [section.replace('-"', '').replace('"', '').split(' ') for section in filter_sections_wanted]
        
        
        url_specific_blacklist = ['https://www.zeit.de/exklusive-zeit-artikel', 'https://www.spiegel.de/__proto_url__', 'https://www.sueddeutsche.de/updates-mobileapps', 'https://www.sueddeutsche.de/updates-rss', 'https://www.sueddeutsche.de/mediadaten']
        section_blacklist = [term for section in filter_sections_wanted_clean for term in section]
        regex_blacklist_sections = ""

        for section in section_blacklist:
            regex_blacklist_sections = f"{regex_blacklist_sections}{section}|" 

        if regex_blacklist_sections[-1] == "|":
            regex_blacklist_sections = regex_blacklist_sections[:-1]
        if len(regex_blacklist_sections) != 0:
            regex_blacklist_sections = fr"\/({regex_blacklist_sections})\/?"

        section_whitelist = ["artikel"]

        regex_whitelist_sections = ""

        for section in section_whitelist:
            regex_whitelist_sections = f"{regex_whitelist_sections}{section}|" 

        if regex_whitelist_sections[-1] == "|":
            regex_whitelist_sections = regex_whitelist_sections[:-1]
        if len(regex_whitelist_sections) != 0:
            regex_whitelist_sections = fr"\/({regex_whitelist_sections})\/?"


        regex_parameters_general = r"((\/.*?){2,}\/$|\/\/www\..*?\..{2,3}\/[^\/]*?$|\/\/www\..*?\..{2}$)"
        regex_parameters_blacklist_sections = fr"({regex_blacklist_sections})"  
        regex_parameters_whitelist_sections = fr"({regex_whitelist_sections})"

        filtered_url_list = []
        removed_url_list = []
        for article in article_url_list:

            not_viable_article_sections = re.search(regex_parameters_blacklist_sections, article) 
            viable_article_sections = re.search(regex_parameters_whitelist_sections, article)
            not_viable_article_general = re.search(regex_parameters_general, article)

            if article not in url_specific_blacklist and viable_article_sections != None:
                filtered_url_list.append(article)
            else:
                if not_viable_article_general == None and not_viable_article_sections == None:
                    filtered_url_list.append(article)
                else: 
                    removed_url_list.append(article)
                    ### if you want to add in an export

        filtered_url_list = list(dict.fromkeys(filtered_url_list))    
        removed = (len(article_url_list)-len(filtered_url_list))
        if removed != 0:
            log.info(f'Filtered out {removed} URLs.')
        else:
            log.error(f'Filtered out no URLs.')
    else:
        filtered_url_list = article_url_list
        log.info('Filtered out no URLs, as intended.')
    return filtered_url_list

### Export
def export_sql(df):

    user = ""
    pw = ""
    db = ""
    host = ""
    port = ""
    uri = f"postgresql+psycopg2://{user}:{pw}@{host}:{port}/{db}"
    alchemyEngine = create_engine(uri) 
    df.to_sql(name="", con=alchemyEngine, if_exists="append", index=False) ## database info

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
        df = df.dropna(how='all')
        kick_list = []
        with open("/data_collection/newsfeedback/default_article_blacklist.txt", "r+") as f: ## to truly make sure no duplicates with kicklist remain
            for line in f:
                kick_list.append(line.rstrip('\n'))

        kick_list.append(homepage_url)
        kick_list.append(homepage_url.replace('www.',''))
        kick_list.append(homepage_url[:-1])
        df_no_dupes = df[~df.url.isin(kick_list)]
        ### add in token count barrier -> ab 100 rein, bis 10.000
        amount_of_articles = df['url'].shape[0]
        df_no_dupes.to_csv(df_path, index=False, mode='a', encoding="utf-8")
        filesize_byte = os.path.getsize(df_path)
        filesize = int(filesize_byte) / 1000
        if filesize <= 10:
            log.warning(f'{amount_of_articles} articles. Caution! Suspiciously small file generated at: {df_path} @ {filesize} KB\n')
        else:
            log.info(f'{amount_of_articles} articles. File generated at: {df_path} @ {filesize} KB\n')
    except Exception as ex:    
        log.error(f'Unexpected error occurred: {ex} File could not be generated.\n')
    try:
        export_sql(df)
    except Exception as ex:    
        log.error(f'Unexpected error occurred: {ex} Data could not be written into database.\n')
    return df_path

### CHAINED PIPELINES

def chained_trafilatura_pipeline(homepage_url, filter_choice, output_folder):
    article_url_list = get_article_urls_trafilatura_pipeline(homepage_url)
    filtered_url_list = filter_urls(article_url_list, filter_choice)
    df = get_article_metadata_chain_trafilatura_pipeline(filtered_url_list)
    df_path = export_dataframe(df, homepage_url, output_folder)
    return df_path

def chained_beautifulsoup_pipeline(homepage_url, filter_choice, output_folder):
    article_url_list = get_article_urls_bs_pipeline(homepage_url)
    filtered_url_list = filter_urls(article_url_list, filter_choice)
    df = get_article_metadata_chain_bs_pipeline(filtered_url_list)
    df_path = export_dataframe(df, homepage_url, output_folder)             
    return df_path

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
    if (answer != "Y" or answer != "y") and answer != "testing_tmp_path":
        pass
    else:
        if answer == 'Y' or answer == 'y':
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
    if (answer != "Y" or answer == 'y') and answer != "testing_tmp_path":
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
    homepage_url_list_og = list(homepage_config.keys())
    homepage_url_list = list(list(dict.fromkeys(homepage_url_list_og)))
    log.info(f"Starting the collection of {len(homepage_url_list)} sources.")
    for homepage_url in homepage_url_list:
        get_pipeline_from_config(homepage_url, output_folder)
        
        
    log.info(f"Finishing up the collection of {len(homepage_url_list)} sources.\n\n")

@cli.command(help="Runs the full pipeline for the URLs saveds in either the user or default "
              "config file on schedule.")
#@click.option('-t', '--hour', default='6',
#              help='Run data extraction once every X hours. This is X, but defaults to 6.')
@click.option('-o', '--output-folder', default='newsfeedback/output',
              help="Defaults to newsfeedback's output folder.")
def get_data(hour, output_folder):
    initiate_data_collection(output_folder)
    ## uncomment if you want to schedule with the schedule library and not cron
    '''schedule.every(int(hour)).hours.do(initiate_data_collection, output_folder)
    while True:
        schedule.run_pending()
        time.sleep(1)'''

if __name__ == "main":
    cli()
