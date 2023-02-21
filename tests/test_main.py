""" Test suite for newsfeedback.main
"""
import pytest, os, re, glob,yaml
import pandas as pd
from click.testing import CliRunner
from _pytest.logging import LogCaptureFixture
from loguru import logger as log
from newsfeedback.main import retrieve_config
from newsfeedback.main import get_article_urls_trafilatura_pipeline, get_articles_trafilatura_pipeline, get_article_metadata_chain_trafilatura_pipeline
from newsfeedback.main import get_article_urls_bs_pipeline, get_articles_bs_pipeline, get_article_metadata_chain_bs_pipeline
from newsfeedback.main import accept_pur_abo_homepage, consent_button_homepage, accept_pur_abo_article, get_pur_abo_article_urls_chain, get_pur_abo_article_metadata_chain
from newsfeedback.main import filter_urls
from newsfeedback.main import chained_trafilatura_pipeline, trafilatura_pipeline, chained_beautifulsoup_pipeline, beautifulsoup_pipeline, chained_purabo_pipeline, purabo_pipeline
from newsfeedback.main import get_pipeline_from_config, pipeline_picker, write_in_config, add_homepage_url

@pytest.fixture
def caplog(caplog: LogCaptureFixture):
    handler_id = log.add(caplog.handler)
    yield caplog
    log.remove(handler_id)

class TestTrafilaturaPipeline(object):
    def test_get_article_urls_trafilatura_pipeline_goodurl(self):
        """ Asserts that a list of articles is extracted from a valid URL via the 
        Trafilatura pipeline. """
        homepage_url = "https://www.spiegel.de/"
        actual = get_article_urls_trafilatura_pipeline(homepage_url)
        not_expected = 0
        message = ("get_article_urls_trafilatura_pipeline(homepage_url) "
                   "returned {0} articles.".format(len(actual)))
        assert len(actual) != not_expected, message
        
    def test_get_article_urls_trafilatura_pipeline_badurl(self):
        """ Asserts that a list of articles is not 
        extracted from an nonvalid URL via the Trafilatura pipeline. """
        homepage_url = "https://www.badische-zeitung.de/"
        actual = get_article_urls_trafilatura_pipeline(homepage_url)
        expected = 0
        message = ("get_article_urls_trafilatura_pipeline(homepage_url) "
                   "returned {0} articles, despite expecting {1}".format(len(actual),expected))
        assert len(actual) == expected, message
    
    def test_get_urls_and_metadatatrafilatura_pipeline_goodurl(self):
        """ Asserts that a list of articles and the corresponding metadata
        are extracted from a valid URL via the Trafilatura pipeline. """
        article_url_list = ["https://www.spiegel.de/panorama/bildung/lehrermangel-grundschule-fuehrt-vier-tage-woche-ein-a-fe57dfef-2078-4db2-8609-ac77697f7a18", "https://www.spiegel.de/wirtschaft/unternehmen/ford-will-2300-jobs-in-koeln-und-aachen-streichen-a-097df534-d74d-4092-8600-a4492ed1198d"]
        actual = get_article_metadata_chain_trafilatura_pipeline(article_url_list)
        not_expected = 0
        message = ("get_article_metadata_chain_trafilatura_pipeline(article_url_list) "
                   "returned {0} articles with metadata.".format(actual.shape[0],not_expected))
        assert actual.shape[0] != not_expected, message        
        
    def test_get_urls_and_metadatatrafilatura_pipeline_badurl(self):
        """ Asserts that neither a list of articles, nor the corresponding metadata
        are extracted from an nonvalid URL via the Trafilatura pipeline. """
        article_url_list = ["https://www.smo-wiki.leibniz-hbi.de/", "https://www.smo-wiki.leibniz-hbi.de/"]
        actual = get_article_metadata_chain_trafilatura_pipeline(article_url_list)
        expected = 0
        log.info(actual)
        message = ("get_article_metadata_chain_trafilatura_pipeline(article_url_list) "
                   "returned {0} articles with metadata, despite expecting {1}, at most.".format(actual.shape[0],expected))
        assert actual.shape[0] == expected, message
    
    def test_trafilatura_pipeline_goodurl(self, tmp_path):
        """ Asserts that the entire Trafilatura pipeline works with the data provided by a valid URL.
        The resulting dataframe is exported into a temporary directory. """
        homepage_url = "https://www.spiegel.de/"
        output_folder = tmp_path / "newsfeedback"
        output_folder.mkdir()
        filter_choice = 'off'
        actual = chained_trafilatura_pipeline(homepage_url, filter_choice, output_folder)
        df_from_file = pd.read_csv(actual)
        message = ("The exported dataframe is empty.")                
        assert df_from_file.shape[0] != 0, message

    def test_trafilatura_pipeline_badurl(self, tmp_path):
        """ Asserts that the entire Trafilatura pipeline works with the data provided by a nonvalid URL.
        The resulting - empty - dataframe is exported into a temporary directory. """
        homepage_url = "https://www.smo-wiki.leibniz-hbi.de/"
        output_folder = tmp_path / "newsfeedback"
        output_folder.mkdir()
        filter_choice = 'off'
        actual = chained_trafilatura_pipeline(homepage_url, filter_choice, output_folder)
        df_from_file = pd.read_csv(actual)
        message = ("The exported dataframe is not empty, despite this being expected.")                
        assert df_from_file.shape[0] == 0, message

class TestBeautifulSoupPipeline(object):
    """ Due to the nature of BeautifulSoup, there are no 'bad URLs', unless they have no a hrefs."""

    def test_get_article_urls_bs_pipeline(self):
        """ Asserts that a list of articles is extracted from a valid URL via the 
        BeautifulSoup pipeline. """
        homepage_url = "https://www.badische-zeitung.de/"
        actual = get_article_urls_bs_pipeline(homepage_url)
        not_expected = 0
        message = ("get_article_urls_bs_pipeline(homepage_url) "
                   "returned {0} article URLs.".format(len(actual)))
        assert len(actual) != not_expected, message

    def test_get_article_metadata_title_date_url_description_bs_pipeline(self):
        """ Asserts that a list of articles and the corresponding metadata
        are extracted from a valid URL via the BeautifulSoup pipeline. """
        article_url_list = ["https://www.badische-zeitung.de/unwetterwarnung-aufgehoben-aber-schnee-und-eis-sollen-ueber-nacht-zurueckkehren", "https://www.badische-zeitung.de/fasnacht-2023-in-freiburg-das-programm-am-fasnets-wochenende"]
        actual = get_article_metadata_chain_bs_pipeline(article_url_list)
        not_expected = 0
        message = ("get_article_metadata_chain_bs_pipeline(article_url_list) "
                   "returned {0} metadata.".format(actual.shape[0]))
        assert actual.shape[0] != not_expected, message

    def test_beautifulsoup_pipeline(self, tmp_path):
        """ Asserts that the entire BeautifulSoup pipeline works with the data provided by a valid URL.
        The resulting dataframe is exported into a temporary directory. """
        homepage_url = "https://www.badische-zeitung.de/"
        output_folder = tmp_path / "newsfeedback"
        output_folder.mkdir()
        filter_choice = 'off'
        actual = chained_beautifulsoup_pipeline(homepage_url, filter_choice, output_folder)
        df_from_file = pd.read_csv(actual)
        message = ("The exported dataframe is empty.")                
        assert df_from_file.shape[0] != 0, message

        

class TestPurAboPipeline(object):
    def test_accept_pur_abo_consent_button(self):
        """ Asserts that the Pur Abo / consent button defined by class name in class_name 
        can be clicked when the website homepage is given. """
        homepage_url = "https://www.zeit.de/"
        class_name = "sp_choice_type_11" # full class names: 'message-component message-button no-children focusable sp_choice_type_11'
        actual = accept_pur_abo_homepage(homepage_url, class_name)
        driver = actual[1]
        driver.quit()
        error_message = 'Element could not be found, connection timed out.'
        message = ("accept_pur_abo_homepage(homepage_url, class_name) "
                  "returned {0}, which is an undesired error message.".format(actual[0]))
        assert actual[0] != error_message, message    
        
    def test_accept_pur_abo_subscription_button(self):
        """ Asserts that, should a different error than the Pur Abo / consent button be clicked, 
        an error is returned. """
        homepage_url = "https://www.zeit.de/"
        class_name = "js-forward-link-purabo" # full class names: 'option__button option__button--pur js-forward-link-purabo'
        actual = accept_pur_abo_homepage(homepage_url, class_name)
        driver = actual[1]
        driver.quit()
        error_message = 'Element could not be found, connection timed out.'
        message = ("accept_pur_abo_homepage(homepage_url, class_name) did not return "
                   "the desired error message, but instead"
                   "{0}".format(actual[0]))
        assert actual[0] == error_message, message   
    
    def test_accept_pur_abo_article_consent_button(self):
        """ Asserts that the Pur Abo / consent button defined by class name in class_name 
        can be clicked when a list of articles is given."""
        article_url_list = ["https://www.zeit.de/zett/politik/2022-12/mihran-dabag-voelkermord-jesiden-bundestag-kriegsgewalt", "https://www.zeit.de/gesellschaft/zeitgeschehen/2023-01/illerkirchberg-mord-buergerdialog-ece-s-vater"]
        class_name = "sp_choice_type_11" # full class names: 'message-component message-button no-children focusable sp_choice_type_11'
        actual = accept_pur_abo_article(article_url_list, class_name)
        driver = actual[1]
        driver.quit()
        error_message = 'Element could not be found, connection timed out.'
        message = ("accept_pur_abo_article(article_url_list, class_name) "
                  "returned {0}, which is an undesired error message.".format(actual[0]))
        assert actual[0] != error_message, message 

    def test_get_pur_abo_article_urls(self):
        """ Asserts that a list of articles is extracted from ZEIT Online via the 
        Pur Abo pipeline. """
        homepage_url = "https://www.zeit.de/"
        class_name = "sp_choice_type_11"
        (text, driver) = accept_pur_abo_homepage(homepage_url, class_name)
        actual = get_pur_abo_article_urls_chain(text, driver)
        driver.quit()
        not_expected = 0
        message = ("get_pur_abo_article_urls_chain(text, driver) "
                   "returned {0} article URLs.".format(len(actual)))
        assert len(actual) != not_expected, message

    def test_get_pur_abo_article_urls_and_metadata(self):
        """ Asserts that a list of articles and the corresponding metadata
        are extracted from ZEIT Online via the Pur Abo pipeline. """
        homepage_url = "https://www.zeit.de/"
        class_name = "sp_choice_type_11"
        (text, driver) = accept_pur_abo_homepage(homepage_url, class_name)
        article_url_list = get_pur_abo_article_urls_chain(text, driver)
        returned_article_url_list = filter_urls(article_url_list, filter_choice='off')
        driver.quit()
        (text, driver) = accept_pur_abo_article(returned_article_url_list, class_name)
        actual = get_pur_abo_article_metadata_chain(homepage_url, driver, returned_article_url_list)
        not_expected = 0
        message = ("get_pur_abo_article_metadata_chain(homepage_url, driver, returned_article_url_list) "
                   "returned {0} articles with metadata.".format(actual.shape[0]))
        assert actual.shape[0] != not_expected, message


class TestFilterPipeline(object):
    ### Not sure if the first two make sense, as the trafilatura pipeline pipeline already 
    ### retrieves viable article URLs. 

    def test_filter_article_urls_trafilatura_pipeline_goodurl(self):
        """ Asserts that a list of filtered articles is extracted from 
        a valid URL via the Trafilatura pipeline. """
        homepage_url = "https://www.spiegel.de/"
        filter_choice = 'on'
        article_url_list = get_article_urls_trafilatura_pipeline(homepage_url)
        actual = filter_urls(article_url_list, filter_choice)
        not_expected = 0 
        message = ("filter_urls(article_url_list) "
                   "returned {0} filtered article URLs.".format(len(actual)))
        assert len(actual) != not_expected, message

    def test_filter_article_urls_trafilatura_pipeline_badurl(self):
        """ Asserts that a list of filtered articles is not extracted from 
        a nonvalid URL via the Trafilatura pipeline. """
        homepage_url = "https://www.badische-zeitung.de/"
        filter_choice = 'on'
        article_url_list = get_article_urls_trafilatura_pipeline(homepage_url)
        actual = filter_urls(article_url_list, filter_choice)
        expected = 0 
        message = ("filter_urls(article_url_list) "
                   "returned {0} filtered article URLs, despite expecting {1}.".format(len(actual),expected))
        assert len(actual) == expected, message    

    def test_filter_article_urls_bs_pipeline(self):
        """ Asserts that a list of filtered articles is extracted from 
        a valid URL via the BeautifulSoup pipeline. """
        homepage_url = "https://www.badische-zeitung.de/"
        filter_choice = 'on'
        article_url_list = get_article_urls_bs_pipeline(homepage_url)
        actual = filter_urls(article_url_list, filter_choice)
        not_expected = 0 
        message = ("filter_urls(article_url_list) "
                   "returned {0} filtered article URLs.".format(len(actual)))
        assert len(actual) != not_expected, message

    def test_filter_article_urls_purabo_pipeline(self):
        """ Asserts that a list of filtered articles is extracted from
        ZEIT Online via the Pur Abo pipeline. """
        homepage_url = "https://www.zeit.de/"
        class_name = "sp_choice_type_11"
        (text, driver) = accept_pur_abo_homepage(homepage_url, class_name)
        article_url_list = get_pur_abo_article_urls_chain(text, driver)
        actual = filter_urls(article_url_list, filter_choice='on')
        driver.quit()
        not_expected = 0
        message = ("filter_urls(article_url_list) "
                   "returned {0} filtered article URLs.".format(actual.shape[0]))
        assert len(actual) != not_expected, message


class TestClickTrafilaturaPipeline(object):
    def test_click_get_articles_trafilatura_pipeline_goodurl(self, caplog):
        """ Asserts that a list of articles is extracted from a valid URL via the 
        Trafilatura pipeline called with Click. """
        runner = CliRunner()
        homepage_url = "'https://www.spiegel.de/'"
        runner.invoke(get_articles_trafilatura_pipeline, f"-u {homepage_url} \n")
        message = ("get_articles_trafilatura_pipeline(homepage_url) "
                   "returned no articles.".format(caplog.text))
        assert "INFO" in caplog.text, message

    def test_click_get_articles_trafilatura_pipeline_badurl(self, caplog):
        """ Asserts that a list of articles is extracted from a nonvalid URL via the 
        Trafilatura pipeline called with Click. """
        runner = CliRunner()
        homepage_url = "'https://www.badische-zeitung.de/'"
        runner.invoke(get_articles_trafilatura_pipeline, f"-u {homepage_url} \n")
        message = ("get_article_urls_trafilatura_pipeline(homepage_url) "
                   "returned articles, despite none being expected.".format(caplog.text))
        assert "ERROR" in caplog.text, message

class TestClickBeautifulSoupPipeline(object):
    def test_click_get_articles_bs_pipeline_goodurl(self, caplog):
        """ Asserts that a list of articles is extracted from a valid URL via the 
        BeautifulSoup pipeline called with Click. """
        runner = CliRunner()
        homepage_url = "'https://www.badische-zeitung.de/'"
        runner.invoke(get_articles_bs_pipeline, f"-u {homepage_url} \n")
        message = ("get_articles_bs_pipeline(homepage_url) "
                   "returned no articles.".format(caplog.text))
        assert "INFO" in caplog.text, message

class TestClickPurAbo(object):
    def test_consent_button_homepage(self, caplog):
        """ Asserts that the Pur Abo / consent button defined by class name in class_name 
        can be clicked when the website homepage is given. This is a Click function."""
        runner = CliRunner()
        homepage_url = "'https://www.zeit.de/'"
        runner.invoke(consent_button_homepage, f"-u {homepage_url} \n")
        message = ("consent_button_homepage(homepage_url, class_name) "
                    "was unable to click the consent button "
                    "on the given homepage. ".format(caplog.text))
        assert "INFO" in caplog.text, message
    
    def test_subscription_button_homepage(self, caplog):
        """ Asserts that, should a different error than the Pur Abo / consent button be clicked, 
        an error is returned. This is a Click function. """
        runner = CliRunner()
        homepage_url = "'https://www.zeit.de/'"
        class_name = "js-forward-link-purabo"
        runner.invoke(consent_button_homepage, f"-u {homepage_url} -c {class_name}\n")
        message = ("consent_button_homepage(homepage_url, class_name) "
                    "was unable to click the subscription button "
                    "on the given homepage.".format(caplog.text))
        assert "ERROR" in caplog.text, message


class TestClickTrafilaturaPipeline(object):
    
    def test_click_trafilatura_chain_goodurl(self, tmp_path):
        """ Asserts that the entire Trafilatura pipeline works with the data provided by a valid URL.
        The resulting dataframe is exported into a temporary directory. This is a Click function."""
        runner = CliRunner()
        homepage_url = "'https://www.spiegel.de/'"
        output_folder = tmp_path / "newsfeedback"
        output_folder.mkdir()
        output_path = f"'{output_folder}'"
        filter_choice = "'off'"
        runner.invoke(trafilatura_pipeline, f"-u {homepage_url} -f {filter_choice} -o {output_path} \n")
        homepage = re.search(r"\..+?\.",f"{homepage_url}").group(0)
        homepage = homepage.replace(".","") 
        output_path = output_path.replace("'", "")
        list_of_files = glob.glob(f'{output_path}/*{homepage}.csv')
        latest_file = max(list_of_files, key=os.path.getctime)
        df_from_file = pd.read_csv(latest_file.replace(r".*?/.*?\\\\",""))
        message = ("The exported dataframe is empty.")                
        assert df_from_file.shape[0] != 0, message

    def test_click_trafilatura_chain_badurl(self, tmp_path):
        """ Asserts that the entire Trafilatura pipeline works with the data provided by a nonvalid URL.
        The resulting - empty - dataframe is exported into a temporary directory. This is a Click function."""
        runner = CliRunner()
        homepage_url = "'https://www.smo-wiki.leibniz-hbi.de/'"
        output_folder = tmp_path / "newsfeedback"
        output_folder.mkdir()
        output_path = f"'{output_folder}'"
        filter_choice = "'off'"
        runner.invoke(trafilatura_pipeline, f"-u {homepage_url} -f {filter_choice} -o {output_path} \n")
        homepage = re.search(r"\..+?\.",f"{homepage_url}").group(0)
        homepage = homepage.replace(".","") 
        output_path = output_path.replace("'", "")
        list_of_files = glob.glob(f'{output_path}/*{homepage}.csv')
        latest_file = max(list_of_files, key=os.path.getctime)
        df_from_file = pd.read_csv(latest_file.replace(r".*?/.*?\\\\",""))
        message = ("The exported dataframe is not empty.")                
        assert df_from_file.shape[0] == 0, message

    def test_click_filter_trafilatura_chain_goodurl(self, tmp_path):
        """ Asserts that the entire filtered Trafilatura pipeline works with the data provided by a valid URL.
        The resulting dataframe is exported into a temporary directory. """
        runner = CliRunner()
        homepage_url = "'https://www.spiegel.de/'"
        output_folder = tmp_path / "newsfeedback"
        output_folder.mkdir()
        output_path = f"'{output_folder}'"
        filter_choice = "'on'"
        runner.invoke(trafilatura_pipeline, f"-u {homepage_url} -f {filter_choice} -o {output_path} \n")
        homepage = re.search(r"\..+?\.",f"{homepage_url}").group(0)
        homepage = homepage.replace(".","") 
        output_path = output_path.replace("'", "")
        list_of_files = glob.glob(f'{output_path}/*{homepage}.csv')
        latest_file = max(list_of_files, key=os.path.getctime)
        df_from_file = pd.read_csv(latest_file.replace(r".*?/.*?\\\\",""))
        message = ("The exported dataframe is empty.")                
        assert df_from_file.shape[0] != 0, message

    def test_click_filter_trafilatura_chain_badurl(self, tmp_path):
        """ Asserts that the entire filtered Trafilatura pipeline works with the data provided by a nonvalid URL.
        The resulting - empty - dataframe is exported into a temporary directory. This is a Click function."""
        runner = CliRunner()
        homepage_url = "'https://www.smo-wiki.leibniz-hbi.de/'"
        output_folder = tmp_path / "newsfeedback"
        output_folder.mkdir()
        output_path = f"'{output_folder}'"
        filter_choice = "'on'"
        runner.invoke(trafilatura_pipeline, f"-u {homepage_url} -f {filter_choice} -o {output_path} \n")
        homepage = re.search(r"\..+?\.",f"{homepage_url}").group(0)
        homepage = homepage.replace(".","") 
        output_path = output_path.replace("'", "")
        list_of_files = glob.glob(f'{output_path}/*{homepage}.csv')
        latest_file = max(list_of_files, key=os.path.getctime)
        df_from_file = pd.read_csv(latest_file.replace(r".*?/.*?\\\\",""))
        message = ("The exported dataframe is not empty.")                
        assert df_from_file.shape[0] == 0, message


class TestClickBeautifulSoupPipeline(object):
    def test_click_bs_chain(self, tmp_path):
        """ Asserts that the entire BeautifulSoup pipeline works with the data provided by a valid URL.
        The resulting dataframe is exported into a temporary directory. This is a Click function."""
        runner = CliRunner()
        homepage_url = "'https://www.badische-zeitung.de/'"
        output_folder = tmp_path / "newsfeedback"
        output_folder.mkdir()
        output_path = f"'{output_folder}'"
        filter_choice = "'off'"
        runner.invoke(beautifulsoup_pipeline, f"-u {homepage_url} -f {filter_choice} -o {output_path} \n")
        homepage = re.search(r"\..+?\.",f"{homepage_url}").group(0)
        homepage = homepage.replace(".","") 
        output_path = output_path.replace("'", "")
        list_of_files = glob.glob(f'{output_path}/*{homepage}.csv')
        latest_file = max(list_of_files, key=os.path.getctime)
        df_from_file = pd.read_csv(latest_file.replace(r".*?/.*?\\\\",""))
        message = ("The exported dataframe is empty.")                
        assert df_from_file.shape[0] != 0, message


    def test_click_filter_bs_chain(self, tmp_path):
        """ Asserts that the entire filtered BeautifulSoup pipeline works with the data provided by a valid URL.
        The resulting dataframe is exported into a temporary directory. This is a Click function."""
        runner = CliRunner()
        homepage_url = "'https://www.badische-zeitung.de/'"
        output_folder = tmp_path / "newsfeedback"
        output_folder.mkdir()
        output_path = f"'{output_folder}'"
        filter_choice = "'on'"
        runner.invoke(beautifulsoup_pipeline, f"-u {homepage_url} -f {filter_choice} -o {output_path} \n")
        homepage = re.search(r"\..+?\.",f"{homepage_url}").group(0)
        homepage = homepage.replace(".","") 
        output_path = output_path.replace("'", "")
        list_of_files = glob.glob(f'{output_path}/*{homepage}.csv')
        latest_file = max(list_of_files, key=os.path.getctime)
        df_from_file = pd.read_csv(latest_file.replace(r".*?/.*?\\\\",""))
        message = ("The exported dataframe is empty.")                
        assert df_from_file.shape[0] != 0, message

class TestClickPurAboPipeline(object):
    def test_click_purabo_chain(self, tmp_path):
        """ Asserts that the entire Pur Abo pipeline works with the data provided by a valid URL.
        The resulting dataframe is exported into a temporary directory. This is a Click function."""
        runner = CliRunner()
        homepage_url = "'https://www.zeit.de/'"
        output_folder = tmp_path / "newsfeedback"
        output_folder.mkdir()
        output_path = f"'{output_folder}'"
        filter_choice = "'off'"
        runner.invoke(purabo_pipeline, f"-u {homepage_url} -f {filter_choice} -o {output_path} \n")
        homepage = re.search(r"\..+?\.",f"{homepage_url}").group(0)
        homepage = homepage.replace(".","") 
        output_path = output_path.replace("'", "")
        list_of_files = glob.glob(f'{output_path}/*{homepage}.csv')
        latest_file = max(list_of_files, key=os.path.getctime)
        df_from_file = pd.read_csv(latest_file.replace(r".*?/.*?\\\\",""))
        message = ("The exported dataframe is empty.")                
        assert df_from_file.shape[0] != 0, message

    def test_click_filter_purabo_chain(self, tmp_path):
        """ Asserts that the entire filtered Pur Abo pipeline works with the data provided by a valid URL.
        The resulting dataframe is exported into a temporary directory. This is a Click function.""" 
        runner = CliRunner()
        homepage_url = "'https://www.zeit.de/'"
        output_folder = tmp_path / "newsfeedback"
        output_folder.mkdir()
        output_path = f"'{output_folder}'"
        filter_choice = "'on'"
        runner.invoke(purabo_pipeline, f"-u {homepage_url} -f {filter_choice} -o {output_path} \n")
        homepage = re.search(r"\..+?\.",f"{homepage_url}").group(0)
        homepage = homepage.replace(".","") 
        output_path = output_path.replace("'", "")
        list_of_files = glob.glob(f'{output_path}/*{homepage}.csv')
        latest_file = max(list_of_files, key=os.path.getctime)
        df_from_file = pd.read_csv(latest_file.replace(r".*?/.*?\\\\",""))
        message = ("The exported dataframe is empty.")                
        assert df_from_file.shape[0] != 0, message

class TestPipelineFromConfig(object):

    def test_retrieve_config_metadata(self):
        """ Asserts that the retrieved metadata config file is the correct one, based on the (non-)existence of a 
        user-generated config file. """
        actual = retrieve_config('metadata')

        if os.path.isfile("newsfeedback/user_metadata_config.yaml"):
            config_file = "newsfeedback/user_metadata_config.yaml"
        else:
            config_file = "newsfeedback/default_metadata_config.yaml"
    
        with open(config_file, "r") as yamlfile:
            data = yaml.load(yamlfile, Loader=yaml.FullLoader)
        message = ("The retrieved file is not identical to the expected file.")
        assert actual == data, message

    def test_retrieve_config_homepage(self):
        """ Asserts that the retrieved homepage config file is the correct one, based on the (non-)existence of a 
        user-generated config file. """
        actual = retrieve_config('homepage')

        if os.path.isfile("newsfeedback/user_homepage_config.yaml"):
            config_file = "newsfeedback/user_homepage_config.yaml"
        else:
            config_file = "newsfeedback/default_homepage_config.yaml"
    
        with open(config_file, "r") as yamlfile:
            data = yaml.load(yamlfile, Loader=yaml.FullLoader)
        message = ("The retrieved file is not identical to the expected file.")
        assert actual == data, message       

    '''    def test_add_homepage_url(self):
        """Asserts that the user is able to add a homepage of their choice to the homepage config. """
        homepage_url = "test_url"
        chosen_pipeline = "'2'"
        filter_option = "'on'"
        runner = CliRunner()
        runner.invoke(add_homepage_url, f"-u '{homepage_url}' -p {chosen_pipeline} -f {filter_option}")
    
        with open("user_homepage_config.yaml", 'r') as yamlfile:
            homepage_config = yaml.load(yamlfile, Loader=yaml.FullLoader)
            data = homepage_config.get(homepage_url)
            print(data)
            if data:
                actual = "Homepage was found in config."
                updated_data = data.pop(homepage_url)
                with open("user_homepage_config.yaml", "w") as yamlfile:
                    yaml.dump(updated_data, yamlfile)    
            else:
                actual = "Homepage not found in config."
        
        with open("user_homepage_config.yaml", 'r+') as yamlfile:
            homepage_config = yaml.load(yamlfile, Loader=yaml.FullLoader)
            data = homepage_config.get(homepage_url)
            if data:
                actual = "Homepage found in config."
                test_data_removed = homepage_config
                del test_data_removed[homepage_url]
                print(test_data_removed)
                yaml.dump(test_data_removed, yamlfile)
            else:
                actual = "Homepage not found in config."

        message = ("Homepage was not added to the config.")
        assert actual == "Homepage found in config.", message'''
        

    
    def test_pipeline_picker_trafilatura(self, tmp_path):
        """ Asserts that that the Trafilatura pipeline is correctly chosne and executed
        from the website config. """
        runner = CliRunner()
        homepage_url = "'https://www.spiegel.de/'"
        output_folder = tmp_path / "newsfeedback"
        output_folder.mkdir()
        output_path = f"'{output_folder}'"
        runner.invoke(pipeline_picker, f"-u {homepage_url} -o {output_path} \n")
        homepage = re.search(r"\..+?\.",f"{homepage_url}").group(0)
        homepage = homepage.replace(".","") 
        output_path = output_path.replace("'", "")
        list_of_files = glob.glob(f'{output_path}/*{homepage}.csv')
        latest_file = max(list_of_files, key=os.path.getctime)
        df_from_file = pd.read_csv(latest_file.replace(r".*?/.*?\\\\",""))
        message = ("The exported dataframe is empty.")                
        assert df_from_file.shape[0] != 0, message
        
    def test_pipeline_picker_beautifulsoup(self, tmp_path):
        """ Asserts that that the BeautifulSoup pipeline is correctly chosne and executed
        from the website config. """
        runner = CliRunner()
        homepage_url = "'https://www.badische-zeitung.de/'"
        output_folder = tmp_path / "newsfeedback"
        output_folder.mkdir()
        output_path = f"'{output_folder}'"
        runner.invoke(pipeline_picker, f"-u {homepage_url} -o {output_path} \n")
        homepage = re.search(r"\..+?\.",f"{homepage_url}").group(0)
        homepage = homepage.replace(".","") 
        output_path = output_path.replace("'", "")
        list_of_files = glob.glob(f'{output_path}/*{homepage}.csv')
        latest_file = max(list_of_files, key=os.path.getctime)
        df_from_file = pd.read_csv(latest_file.replace(r".*?/.*?\\\\",""))
        message = ("The exported dataframe is empty.")                
        assert df_from_file.shape[0] != 0, message
    
    def test_pipeline_picker_purabo(self, tmp_path):
        """ Asserts that that the Pur Abo pipeline is correctly chosne and executed
        from the website config. """
        runner = CliRunner()
        homepage_url = "'https://www.zeit.de/'"
        output_folder = tmp_path / "newsfeedback"
        output_folder.mkdir()
        output_path = f"'{output_folder}'"
        runner.invoke(pipeline_picker, f"-u {homepage_url} -o {output_path} \n")
        homepage = re.search(r"\..+?\.",f"{homepage_url}").group(0)
        homepage = homepage.replace(".","") 
        output_path = output_path.replace("'", "")
        list_of_files = glob.glob(f'{output_path}/*{homepage}.csv')
        latest_file = max(list_of_files, key=os.path.getctime)
        df_from_file = pd.read_csv(latest_file.replace(r".*?/.*?\\\\",""))
        message = ("The exported dataframe is empty.")                
        assert df_from_file.shape[0] != 0, message
        
    def test_pipeline_picker_all(self, tmp_path):
        """ Asserts that that the correct pipelines for the given URLs (all in the config) are chosen and executed
        from the website config. """
        list_homepage_url = ['https://www.zeit.de/','https://www.spiegel.de/','https://www.badische-zeitung.de/','https://www.bild.de/','https://www.faz.net/','https://www.focus.de/','https://www.handelsblatt.com/','https://www.n-tv.de/','https://www.rnd.de/','https://www.rtl.de/','https://www.stern.de/','https://www.sueddeutsche.de/','https://www.t-online.de/','https://www.upday.com/de/','https://www.welt.de/','https://www.merkur.de/','https://www.tz.de/','https://www.fr.de/']
        runner = CliRunner()
        list_empty_df = []
        output_folder = tmp_path / "newsfeedback"
        output_folder.mkdir()
        for homepage_url in list_homepage_url:
            homepage_name = re.search(r"\..+?\.",f"{homepage_url}").group(0)
            homepage_name = homepage_name.replace(".","") 
            output_path = f"'{output_folder}'"
            runner.invoke(pipeline_picker, f"-u {homepage_url} -o {output_path} \n")
            output_path = output_path.replace("'", "")
            list_of_files = glob.glob(f'{output_path}/*{homepage_name}.csv')
            latest_file = max(list_of_files, key=os.path.getctime)
            df_from_file = pd.read_csv(latest_file.replace(r".*?/.*?\\\\",""))
            if df_from_file.shape[0] == 0:
                list_empty_df.append(latest_file)
        message = (f"At least one exported dataframe is empty: {list_empty_df}")                
        assert len(list_empty_df) == 0, message

    def test_pipeline_picker_not_in_config(self, caplog):
        """ Asserts that that the correct pipelines for a URL that is not in the config are chosen and executed
        from the website config. """
        runner = CliRunner()
        homepage_url = "'https://www.smo-wiki.leibniz-hbi.de/'"
        runner.invoke(pipeline_picker, f"-u {homepage_url} \n")
        message = ("The given URL was already in the config file, despite being expected not to be.".format(caplog.text))                
        assert "ERROR" in caplog.text, message

    