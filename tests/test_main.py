""" Test suite for newsfeedback.main
"""
import pytest, os, re, glob, click
import pandas as pd
from click.testing import CliRunner
from _pytest.logging import LogCaptureFixture
from loguru import logger as log
from newsfeedback.main import get_article_urls_trafilatura_pipeline, get_articles_trafilatura_pipeline, get_article_metadata_chain_trafilatura_pipeline
from newsfeedback.main import get_article_urls_bs_pipeline, get_articles_bs_pipeline, get_article_metadata_chain_bs_pipeline
from newsfeedback.main import accept_pur_abo_homepage, consent_button_homepage, accept_pur_abo_article, consent_button_article, get_pur_abo_article_metadata_chain
from newsfeedback.main import filter_urls, export_dataframe
from newsfeedback.main import chained_trafilatura_pipeline, trafilatura_pipeline, chained_beautifulsoup_pipeline, beautifulsoup_pipeline, chained_purabo_pipeline, purabo_pipeline
from newsfeedback.main import get_pipeline_from_config, pipeline_picker, write_in_config, add_homepage_url

@pytest.fixture
def caplog(caplog: LogCaptureFixture):
    handler_id = log.add(caplog.handler)
    yield caplog
    log.remove(handler_id)

class TestTrafilaturaPipeline(object):
    def test_get_article_urls_trafilatura_pipeline_goodurl(self):
        homepage_url = "https://www.spiegel.de/"
        actual = get_article_urls_trafilatura_pipeline(homepage_url)
        not_expected = 0
        message = ("get_article_urls_trafilatura_pipeline(homepage_url) "
                   "returned {0} articles.".format(len(actual)))
        assert len(actual) != not_expected, message
        
    def test_get_article_urls_trafilatura_pipeline_badurl(self):
        homepage_url = "https://www.badische-zeitung.de/"
        actual = get_article_urls_trafilatura_pipeline(homepage_url)
        expected = 0
        message = ("get_article_urls_trafilatura_pipeline(homepage_url) "
                   "returned {0} articles, despite expecting {1}".format(len(actual),expected))
        assert len(actual) == expected, message
    
    def test_get_article_url_and_metadata_title_date_url_description_trafilatura_pipeline_goodurl(self):
        article_url_list = ["https://www.spiegel.de/panorama/bildung/lehrermangel-grundschule-fuehrt-vier-tage-woche-ein-a-fe57dfef-2078-4db2-8609-ac77697f7a18", "https://www.spiegel.de/wirtschaft/unternehmen/ford-will-2300-jobs-in-koeln-und-aachen-streichen-a-097df534-d74d-4092-8600-a4492ed1198d"]
        actual = get_article_metadata_chain_trafilatura_pipeline(article_url_list)
        not_expected = 0
        message = ("get_article_metadata_trafilatura_pipeline(article_url) "
                   "returned {0} articles with metadata.".format(actual.shape[0],not_expected))
        assert actual.shape[0] == not_expected, message        
        
    def test_get_article_url_and_metadata_title_date_url_description_trafilatura_pipeline_badurl(self):
        article_url_list = ["https://smo-wiki.leibniz-hbi.de/", "https://smo-wiki.leibniz-hbi.de/"]
        actual = get_article_metadata_chain_trafilatura_pipeline(article_url_list)
        expected = 0
        message = ("get_article_metadata_trafilatura_pipeline(article_url) "
                   "returned {0} articles with metadata, despite expecting {1}.".format(actual.shape[0],expected))
        assert actual.shape[0] == expected, message     
    
    def test_beautifulsoup_pipeline_goodurl(self, tmp_path):
        homepage_url = "https://www.spiegel.de/"
        output_folder = tmp_path / "newsfeedback"
        output_folder.mkdir()
        filter_choice = 'off'
        actual = chained_beautifulsoup_pipeline(homepage_url, filter_choice, output_folder)
        df_from_file = pd.read_csv(actual)
        message = ("The exported dataframe is empty.")                
        assert df_from_file.shape[0] != 0, message

    def test_beautifulsoup_pipeline_badurl(self, tmp_path):
        homepage_url = "https://smo-wiki.leibniz-hbi.de/"
        output_folder = tmp_path / "newsfeedback"
        output_folder.mkdir()
        filter_choice = 'off'
        actual = chained_beautifulsoup_pipeline(homepage_url, filter_choice, output_folder)
        df_from_file = pd.read_csv(actual)
        message = ("The exported dataframe is not empty, despite this being expected.")                
        assert df_from_file.shape[0] == 0, message

class TestFilterPipeline(object):
    ### Not sure if the first two make sense, as the trafilatura pipeline pipeline already 
    ### retrieves viable article URLs. 

    def test_filter_article_urls_trafilatura_pipeline_goodurl(self):
        homepage_url = "https://www.spiegel.de/"
        filter_choice = 'on'
        article_url_list = get_article_urls_trafilatura_pipeline(homepage_url)
        actual = filter_urls(article_url_list, filter_choice)
        not_expected = 0 
        message = ("filter_urls(article_url_list) "
                   "returned {0} filtered article URLs.".format(len(actual)))
        assert len(actual) != not_expected, message

    def test_filter_article_urls_trafilatura_pipeline_badurl(self):
        homepage_url = "https://www.badische-zeitung.de/"
        filter_choice = 'on'
        article_url_list = get_article_urls_trafilatura_pipeline(homepage_url)
        actual = filter_urls(article_url_list, filter_choice)
        expected = 0 
        message = ("filter_urls(article_url_list) "
                   "returned {0} filtered article URLs, despite expecting {1}.".format(len(actual),expected))
        assert len(actual) == expected, message    

    def test_filter_article_urls_bs_pipeline_goodurl(self):
        homepage_url = "https://www.badische-zeitung.de/"
        filter_choice = 'on'
        article_url_list = get_article_urls_bs_pipeline(homepage_url)
        actual = filter_urls(article_url_list, filter_choice)
        not_expected = 0 
        message = ("filter_urls(article_url_list) "
                   "returned {0} filtered article URLs.".format(len(actual)))
        assert len(actual) != not_expected, message

class TestBeautifulSoupPipeline(object):
    def test_get_article_urls_bs_pipeline_goodurl(self):
        homepage_url = "https://www.badische-zeitung.de/"
        actual = get_article_urls_bs_pipeline(homepage_url)
        not_expected = 0
        message = ("get_article_urls_bs_pipeline(homepage_url) "
                   "returned {0} article URLs.".format(len(actual)))
        assert len(actual) != not_expected, message

    ### would be good to find an URL without any a hrefs to test the opposing case

    def test_get_article_metadata_title_date_url_description_bs_pipeline_goodurl(self):
        """ Asserts whether the desired metadata (in this case: Title, Date, URL, Description) 
        can be extracted from an article URL that was retrieved from the homepage whose articles
        can only be extracted with beautifulsoup.
        """
        article_url = "https://www.badische-zeitung.de/unwetterwarnung-aufgehoben-aber-schnee-und-eis-sollen-ueber-nacht-zurueckkehren"
        actual = get_article_metadata_bs_pipeline(article_url)
        not_expected = 0
        message = ("get_article_metadata_bs_pipeline(article_url) "
                   "returned {0} metadata.".format(len(actual)))
        assert len(actual) != not_expected, message

    def test_get_article_metadata_complete_bs_pipeline(self):
        article_url = "https://www.badische-zeitung.de/unwetterwarnung-aufgehoben-aber-schnee-und-eis-sollen-ueber-nacht-zurueckkehren"
        actual = get_article_metadata_bs_pipeline(article_url)
        not_expected = 0
        message = ("get_article_metadata_bs_pipeline(article_url) "
                   "returned {0} metadata.".format(len(actual)))
        assert len(actual) != not_expected, message

    def test_get_article_url_and_metadata_title_date_url_description_bs_pipeline_goodurl(self):
        homepage_url = "https://www.badische-zeitung.de/"
        actual = get_article_urls_and_metadata_bs_pipeline(homepage_url)
        not_expected = 0
        message = ("get_article_urls_and_metadata_bs_pipeline(article_url) "
                   "returned {0} articles with metadata.".format(actual.shape[0]))
        assert actual.shape[0] != not_expected, message          

class TestWebsiteSpecificFunctions(object):
    def test_accept_pur_abo_consent_button(self):
        homepage_url = "https://www.zeit.de/"
        class_name = "sp_choice_type_11" # full class names: 'message-component message-button no-children focusable sp_choice_type_11'
        actual = accept_pur_abo_homepage(homepage_url, class_name)
        driver = actual[1]
        driver.quit()
        error_message = 'Element could not be found, connection timed out.'
        message = ("accept_pur_abo(homepage_url, class_name) "
                  "returned {0}, which is an undesired error message.".format(actual[0]))
        assert actual[0] != error_message, message    
        
    def test_accept_pur_abo_subscription_button(self):
        homepage_url = "https://www.zeit.de/"
        class_name = "js-forward-link-purabo" # full class names: 'option__button option__button--pur js-forward-link-purabo'
        actual = accept_pur_abo_homepage(homepage_url, class_name)
        driver = actual[1]
        driver.quit()
        error_message = 'Element could not be found, connection timed out.'
        message = ("accept_pur_abo(homepage_url, class_name) did not return "
                   "the desired error message, but instead"
                   "{0}".format(actual[0]))
        assert actual[0] == error_message, message   
    
    def test_accept_pur_abo_article_consent_button(self):
        article_url_list = ["https://www.zeit.de/zett/politik/2022-12/mihran-dabag-voelkermord-jesiden-bundestag-kriegsgewalt", "https://www.zeit.de/gesellschaft/zeitgeschehen/2023-01/illerkirchberg-mord-buergerdialog-ece-s-vater"]
        class_name = "sp_choice_type_11" # full class names: 'message-component message-button no-children focusable sp_choice_type_11'
        actual = accept_pur_abo_article(article_url_list, class_name)
        driver = actual[1]
        driver.quit()
        error_message = 'Element could not be found, connection timed out.'
        message = ("accept_pur_abo(homepage_url, class_name) "
                  "returned {0}, which is an undesired error message.".format(actual[0]))
        assert actual[0] != error_message, message 

    def test_get_pur_abo_article_urls(self):
        homepage_url = "https://www.zeit.de/"
        class_name = "sp_choice_type_11"
        actual = get_pur_abo_article_urls(homepage_url, class_name)
        not_expected = 0
        message = ("get_pur_abo_article_urls(homepage_url, class_name) "
                   "returned {0} article URLs.".format(len(actual)))
        assert len(actual) != not_expected, message

    def test_get_pur_abo_article_urls_and_metadata(self):
        homepage_url = "https://www.zeit.de/"
        class_name = "sp_choice_type_11"
        actual = get_pur_abo_article_urls_and_metadata(homepage_url, class_name)
        not_expected = 0
        message = ("get_pur_abo_article_urls_and_metadata(homepage_url, class_name) "
                   "returned {0} articles with metadata.".format(actual.shape[0]))
        assert actual.shape[0] != not_expected, message

    def get_pur_abo_filtered_article_urls_and_metadata(self):
        homepage_url = "https://www.zeit.de/"
        class_name = "sp_choice_type_11"
        actual = get_pur_abo_filtered_article_urls_and_metadata(homepage_url, class_name)
        not_expected = 0
        message = ("get_pur_abo_filtered_article_urls_and_metadata(homepage_url, class_name) "
                   "returned {0} filtered articles with metadata.".format(actual.shape[0]))
        assert actual.shape[0] != not_expected, message

class TestClickTrafilaturaPipeline(object):
    def test_click_get_articles_trafilatura_pipeline_goodurl(self, caplog):
        runner = CliRunner()
        homepage_url = "'https://www.spiegel.de/'"
        runner.invoke(get_articles_trafilatura_pipeline, f"-u {homepage_url} \n")
        message = ("get_articles_trafilatura_pipeline(homepage_url) "
                   "returned no articles.".format(caplog.text))
        assert "INFO" in caplog.text, message

    def test_click_get_articles_trafilatura_pipeline_badurl(self, caplog):
        runner = CliRunner()
        homepage_url = "'https://www.badische-zeitung.de/'"
        runner.invoke(get_articles_trafilatura_pipeline, f"-u {homepage_url} \n")
        message = ("get_article_urls_trafilatura_pipeline(homepage_url) "
                   "returned articles, despite none being expected.".format(caplog.text))
        assert "ERROR" in caplog.text, message

    def test_click_get_article_metadata_title_date_url_description_trafilatura_pipeline_goodurl(self, caplog):
        runner = CliRunner()
        article_url = "'https://www.spiegel.de/netzwelt/apps/elon-musk-hetzt-auf-twitter-gegen-anthony-fauci-und-die-queere-community-und-wird-ausgebuht-a-edd3c470-12cb-485d-a6f9-266dc94279de'"
        runner.invoke(get_metadata_trafilatura_pipeline, f"-a {article_url} \n")
        message = ("get_metadata_trafilatura_pipeline(article_url) "
                   "returned no metadata.".format(caplog.text))
        assert "INFO" in caplog.text, message


    def test_click_get_article_metadata_title_date_url_description_trafilatura_pipeline_badurl(self, caplog):
        runner = CliRunner()
        article_url = "'https://hans-bredow-institut.de/'"
        runner.invoke(get_metadata_trafilatura_pipeline, f"-a {article_url} \n")
        message = ("get_metadata_trafilatura_pipeline(article_url) "
                   "returned metadata, despite none being expected.".format(caplog.text))
        assert "ERROR" in caplog.text, message    
    
    def test_click_get_both_goodurl(self, caplog):
        runner = CliRunner()
        homepage_url = "'https://www.spiegel.de/'"
        runner.invoke(get_both_trafilatura_pipeline, f"-u {homepage_url} \n")
        message = ("get_both_trafilatura_pipeline(homepage_url) "
                   "returned no articles with metadata.".format(caplog.text))
        assert "INFO" in caplog.text, message
        
    def test_click_get_both_badurl(self, caplog):
        runner = CliRunner()
        homepage_url = "'https://smo-wiki.leibniz-hbi.de/'"
        runner.invoke(get_both_trafilatura_pipeline, f"-u {homepage_url} \n")
        message = ("get_both_trafilatura_pipeline(homepage_url) "
                   "returned articles with metadata, despite none being expected.".format(caplog.text))
        assert "ERROR" in caplog.text, message

class TestClickChainPipelines(object):
    def test_pipeline_picker_trafilatura(self, tmp_path):
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

    def test_click_trafilatura_chain_goodurl(self, tmp_path):
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
        runner = CliRunner()
        homepage_url = "'https://smo-wiki.leibniz-hbi.de/'"
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

    def test_click_bs_chain(self, tmp_path):
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

    def test_click_filter_trafilatura_chain_goodurl(self, tmp_path):
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
        runner = CliRunner()
        homepage_url = "'https://smo-wiki.leibniz-hbi.de/'"
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

    def test_click_filter_bs_chain(self, tmp_path):
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

    def test_click_purabo_chain(self, tmp_path):
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

class TestClickBeautifulSoupPipeline(object):
    def test_click_get_articles_bs_pipeline_goodurl(self, caplog):
        runner = CliRunner()
        homepage_url = "'https://www.badische-zeitung.de/'"
        runner.invoke(get_articles_bs_pipeline, f"-u {homepage_url} \n")
        message = ("get_articles_bs_pipeline(homepage_url) "
                   "returned no articles.".format(caplog.text))
        assert "INFO" in caplog.text, message

    def test_click_get_article_metadata_title_date_url_description_bs_pipeline_goodurl(self, caplog):
        runner = CliRunner()
        article_url = "'https://www.badische-zeitung.de/unwetterwarnung-aufgehoben-aber-schnee-und-eis-sollen-ueber-nacht-zurueckkehren'"
        runner.invoke(get_metadata_bs_pipeline, f"-a {article_url} \n")
        message = ("get_metadata_bs_pipeline(article_url) "
                   "returned no metadata.".format(caplog.text))
        assert "INFO" in caplog.text, message

    def test_click_get_both_bs_pipeline_goodurl(self, caplog):
        runner = CliRunner()
        homepage_url = "'https://www.badische-zeitung.de/'"
        runner.invoke(get_both_bs_pipeline, f"-u {homepage_url} \n")
        message = ("get_both_bs_pipeline(homepage_url) "
                   "returned no articles with metadata.".format(caplog.text))
        assert "INFO" in caplog.text, message

class TestClickFilter(object):
    def test_filter_urls(self, caplog):
        runner = CliRunner()
        homepage_url = "'https://www.badische-zeitung.de/'"
        runner.invoke(filter_articles, f"-u {homepage_url} \n")
        message = ("filter_articles(homepage_url) "
                   "removed no articles.".format(caplog.text))
        assert "INFO" in caplog.text, message
    
    def test_filter_both_trafilatura_pipeline_goodurl(self, caplog):
        runner = CliRunner()
        homepage_url = "'https://www.spiegel.de/'"
        runner.invoke(filter_both_trafilatura_pipeline, f"-u {homepage_url} \n")
        message = ("filter_both_trafilatura_pipeline(homepage_url) "
                   "removed no articles.".format(caplog.text))
        assert "INFO" in caplog.text, message

    def test_filter_both_trafilatura_pipeline_badurl(self, caplog):
        runner = CliRunner()
        homepage_url = "'https://www.badische-zeitung.de/'"
        runner.invoke(filter_both_trafilatura_pipeline, f"-u {homepage_url} \n")
        message = ("filter_both_trafilatura_pipeline(homepage_url) "
                   "returned articles, despite none being expected.".format(caplog.text))
        assert "ERROR" in caplog.text, message

    def test_filter_both_bs_pipeline_goodurl(self, caplog):
        runner = CliRunner()
        homepage_url = "'https://www.badische-zeitung.de/'"
        runner.invoke(filter_both_bs_pipeline, f"-u {homepage_url} \n")
        message = ("filter_both_bs_pipeline(homepage_url) "
                   "removed no articles.".format(caplog.text))
        assert "INFO" in caplog.text, message

    class TestClickSiteSpecific(object):
        def test_consent_button_homepage(self, caplog):
            runner = CliRunner()
            homepage_url = "'https://www.zeit.de/'"
            runner.invoke(consent_button_homepage, f"-u {homepage_url} \n")
            message = ("consent_button_homepage(homepage_url, class_name) "
                       "was unable to click the consent button "
                       "on the given homepage. ".format(caplog.text))
            assert "INFO" in caplog.text, message
        
        def test_subscription_button_homepage(self, caplog):
            runner = CliRunner()
            homepage_url = "'https://www.zeit.de/'"
            class_name = "js-forward-link-purabo"
            runner.invoke(consent_button_homepage, f"-u {homepage_url} -c {class_name}\n")
            message = ("consent_button_homepage(homepage_url, class_name) "
                       "was unable to click the subscription button "
                       "on the given homepage.".format(caplog.text))
            assert "ERROR" in caplog.text, message

        def test_consent_articles(self, caplog):
            runner = CliRunner()
            homepage_url = "'https://www.zeit.de/'"
            runner.invoke(consent_articles, f"-u {homepage_url} \n")
            message = ("consent_articles(homepage_url) "
                       "was unable to return article URLs "
                       "from the given homepage.".format(caplog.text)) 
            assert "INFO" in caplog.text, message

        def test_consent_both(self, caplog):
            runner = CliRunner()
            homepage_url = "'https://www.zeit.de/'"
            runner.invoke(consent_both, f"-u {homepage_url} \n")
            message = ("consent_both(homepage_url) "
                       "was unable to return articles with metadata from "
                       "the given homepage.".format(caplog.text))             
            assert "INFO" in caplog.text, message

        def test_filter_consent_both(self, caplog):
            runner = CliRunner()
            homepage_url = "'https://www.zeit.de/'"
            runner.invoke(filter_consent_both, f"-u {homepage_url} \n")
            message = ("consent_articles(homepage_url) "
                       "was unable to return filtered articles with metadata from "
                       "the given homepage.".format(caplog.text)) 
            assert "INFO" in caplog.text, message

