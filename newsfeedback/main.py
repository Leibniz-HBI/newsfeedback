import trafilatura, click, re, time, yaml, os, schedule, requests, random, decimal
import pandas as pd
from pathlib import Path
from trafilatura import feeds
from loguru import logger as log
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException


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



def get_article_metadata_chain_trafilatura_pipeline(article_url_list):
    metadata_config = retrieve_config("metadata")
    metadata_wanted = [k for k,v in metadata_config.items() if v == True]
    metadata_wanted.append('datetime')
    article_list = []
    for article_url in article_url_list:
        downloaded = trafilatura.fetch_url(article_url)
        metadata = trafilatura.bare_extraction(downloaded, only_with_metadata=True, include_links=True)
        if metadata is not None:
            metadata = metadata.as_dict()
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
        sites_blocked_trafilatura = ["https://www.spiegel.de/"]
        sites_requiring_javascript = ["https://www.handelsblatt.com/"]
        if homepage not in sites_blocked_trafilatura and homepage not in sites_requiring_javascript:
            downloaded = trafilatura.fetch_url(homepage)
        else:
            r = requests.get(homepage, timeout=5)
            if r.status_code == requests.codes.ok:                
                downloaded = r.text
                r.close()
                time.sleep(float(decimal.Decimal(random.randrange(100, 400))/100))
            else:
                r.raise_for_status()
                downloaded = ""
            
            javascript_search = re.search('enable JavaScript', downloaded)
            if javascript_search:
                log.info(f"{homepage}: turning on JavaScript.")
                options = webdriver.ChromeOptions()
                options.add_argument('--headless=new') # comment out if you want to see what's happening
                options.add_argument('--log-level=3')
                options.add_argument('--lang=en')
                options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0')
                options.add_experimental_option('excludeSwitches', ['enable-logging'])
                options.add_argument('--enable-javascript')              
                driver = webdriver.Chrome(options=options)
                driver.get(homepage)
                downloaded = driver.page_source
                driver.quit()
        homepage_url = homepage
    else:
        downloaded = homepage
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
                double_url_check = re.search(r"(\/{2}www\..*?){2}", http_url)
                if double_url_check:
                    http_url = re.sub(r"\/{2}.*?\/{2}", "//", http_url)
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


def get_article_metadata_chain_bs_pipeline(article_url_list):
    metadata_config = retrieve_config("metadata")
    metadata_wanted = [k for k,v in metadata_config.items() if v == True]
    article_list = []
    metadata_wanted.append('datetime')

    for article in article_url_list:

        if len(article) < 300:
            sites_blocked_trafilatura = ["https://www.spiegel.de/"]
            sites_requiring_javascript = ["https://www.handelsblatt.com/"]

            homepage_finder = re.match(r".*?//www\..*?\..{2,3}/?", article)
            homepage_found = homepage_finder.group()
            if homepage_found not in sites_blocked_trafilatura and homepage_found not in sites_requiring_javascript:
                downloaded = trafilatura.fetch_url(article)
            else:
                if homepage_found not in sites_requiring_javascript:
                    r = requests.get(article, timeout=5)
                    #homepage_status = r.status_code
                    if r.status_code == requests.codes.ok:                
                        downloaded = r.text
                        r.close()
                        time.sleep(float(decimal.Decimal(random.randrange(100, 400))/100)) # randomize float

                    else:
                        r.raise_for_status()
                else:
                    options = webdriver.ChromeOptions()
                    options.add_argument('--headless=new') # comment out if you want to see what's happening
                    options.add_argument('--log-level=3')
                    options.add_argument('--lang=en')
                    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0')
                    options.add_experimental_option('excludeSwitches', ['enable-logging'])
                    options.add_argument('--enable-javascript')              
                    driver = webdriver.Chrome(options=options)
                    driver.delete_all_cookies()

                    if article == article_url_list[0]:
                        driver.get(article) 
                        downloaded = driver.page_source
                    else:
                        driver.execute_script("window.open('" + str(article) + "');")
                        time.sleep(float(decimal.Decimal(random.randrange(100, 400))/100)) # randomize float
                        if len(driver.window_handles) != 1:
                            driver.switch_to.window(window_name=driver.window_handles[0])
                            time.sleep(float(decimal.Decimal(random.randrange(100, 400))/100))
                            driver.close()
                            driver.switch_to.window(window_name=driver.window_handles[0])
                            try:        
                                downloaded = driver.page_source            
                                time.sleep(float(decimal.Decimal(random.randrange(100, 400))/100)) # randomize float
                                
                            except Exception:
                                downloaded == None
                        else:
                            downloaded == None
                    driver.quit()

                
        else:
            downloaded = article
        if downloaded != None:
            javascript_search = re.match('enable Javascript', downloaded)
            if javascript_search:
                options = webdriver.ChromeOptions()
                options.add_argument('headless=new') # comment out if you want to see what's happening
                options.add_argument('--log-level=3')
                options.add_argument("--enable-javascript")              
                options.add_argument('--lang=en')
                options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0')
                options.add_experimental_option('excludeSwitches', ['enable-logging'])
                driver = webdriver.Chrome(options=options)
                driver.delete_all_cookies()
                downloaded = driver.page_source
                driver.quit()
            metadata = trafilatura.bare_extraction(downloaded, only_with_metadata=True, include_links=False, include_comments=True)
            if metadata != None:
                metadata = metadata.as_dict()
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


### Filter-related functions

def filter_urls(article_url_list, filter_choice):
    ### later this url blacklist will be modular, same with the regex parameters
    url_specific_blacklist = ['https://www.zeit.de/exklusive-zeit-artikel', 'https://www.spiegel.de/__proto_url__', 'https://www.sueddeutsche.de/updates-mobileapps', 'https://www.sueddeutsche.de/updates-rss', 'https://www.sueddeutsche.de/mediadaten']
    section_blacklist = ["vermischtes", "impressum", "games", "dienste", "auto", "karriere", "familie", "fotostrecke", "service", "raetsel", "impressum", "updates-.*?", "ratgeber",
                        "gesundheit", "fuermich", "thema", "kontakt", "deinspiegel", "spiegel", "sport", "reise", "start", "stil", "tests", "mediadaten", "produktempfehlung",
                        "gutscheine", "app", "consent", "sub", "elibrary"] # offload into a config at some point, complete with synonyms for term
    section_whitelist = ["artikel"]

    regex_blacklist_sections = ""

    for section in section_blacklist:
        regex_blacklist_sections = f"{regex_blacklist_sections}{section}|" 

    if regex_blacklist_sections[-1] == "|":
        regex_blacklist_sections = regex_blacklist_sections[:-1]
    if len(regex_blacklist_sections) != 0:
        regex_blacklist_sections = fr"\/({regex_blacklist_sections})\/?"


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

    
                   
    if filter_choice == 'on': 
        filtered_url_list = []
        for article in article_url_list:

            not_viable_article_sections = re.search(regex_parameters_blacklist_sections, article) 
            viable_article_sections = re.search(regex_parameters_whitelist_sections, article)
            not_viable_article_general = re.search(regex_parameters_general, article)

            if article not in url_specific_blacklist and viable_article_sections != None:
                #print(f"P1 - {article}")
                filtered_url_list.append(article)
            else:
                if not_viable_article_general == None and not_viable_article_sections == None:
                    #print(f"P2 - {article}")
                    filtered_url_list.append(article)
            #else:

            ## export to txt or csv or something - filter overview
        filtered_url_list = list(dict.fromkeys(filtered_url_list))    
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