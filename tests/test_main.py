""" Test suite for newsfeedback.main
"""
import pytest, sys
import pandas as pd
from click.testing import CliRunner
from _pytest.logging import LogCaptureFixture
from loguru import logger as log
from newsfeedback.main import get_article_urls_trafilatura_pipeline, get_article_metadata_trafilatura_pipeline, get_article_urls_and_metadata_trafilatura_pipeline
from newsfeedback.main import get_article_urls_bs_pipeline, get_article_metadata_bs_pipeline, get_article_urls_and_metadata_bs_pipeline
from newsfeedback.main import filter_urls, get_filtered_article_urls_and_metadata_trafilatura_pipeline, get_filtered_article_urls_and_metadata_bs_pipeline
from newsfeedback.main import export_dataframe
from newsfeedback.main import accept_pur_abo_homepage, accept_pur_abo_article, get_pur_abo_article_urls, get_pur_abo_article_urls_and_metadata, get_pur_abo_filtered_article_urls_and_metadata
from newsfeedback.main import get_articles_trafilatura_pipeline, get_metadata_trafilatura_pipeline, get_both_trafilatura_pipeline
from newsfeedback.main import get_articles_bs_pipeline,  get_metadata_bs_pipeline, get_both_bs_pipeline
from newsfeedback.main import filter_articles, filter_both_trafilatura_pipeline, filter_both_bs_pipeline
from newsfeedback.main import consent_button_homepage, consent_articles, consent_both, filter_consent_both

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
    
    def test_get_article_metadata_title_date_url_description_trafilatura_pipeline_goodurl(self):
        """ Asserts whether the desired metadata (in this case: Title, Date, URL, Description) 
        can be extracted from an article
        """
        article_url = "https://www.spiegel.de/netzwelt/apps/elon-musk-hetzt-auf-twitter-gegen-anthony-fauci-und-die-queere-community-und-wird-ausgebuht-a-edd3c470-12cb-485d-a6f9-266dc94279de"
        metadata_wanted = ['title', 'date', 'url', 'description']
        actual = get_article_metadata_trafilatura_pipeline(article_url, metadata_wanted)
        not_expected = 0
        message = ("get_article_metadata_trafilatura_pipeline(article_url, metadata_wanted) "
                   "returned {0} metadata".format(len(actual)))
        assert len(actual) != not_expected, message

    def test_get_article_metadata_complete_trafilatura_pipeline(self):
        article_url = "https://www.spiegel.de/netzwelt/apps/elon-musk-hetzt-auf-twitter-gegen-anthony-fauci-und-die-queere-community-und-wird-ausgebuht-a-edd3c470-12cb-485d-a6f9-266dc94279de"
        metadata_wanted = "['title', 'author', 'url', 'hostname', 'description', 'sitename', 'date', 'categories', 'tags', 'fingerprint', 'id', 'license', 'body', 'comments', 'commentsbody', 'raw_text', 'text', 'language']"
        actual = get_article_metadata_trafilatura_pipeline(article_url, metadata_wanted)
        not_expected = 0
        message = ("get_article_metadata_trafilatura_pipeline(article_url, metadata_wanted) "
                   "returned {0} articles with metadata.".format(len(actual)))
        assert len(actual) != not_expected, message
       
    def test_get_article_metadata_title_date_url_description_trafilatura_pipeline_badurl(self):        
        article_url = "https://hans-bredow-institut.de/"
        metadata_wanted = ['title', 'date', 'url', 'description']
        actual = get_article_metadata_trafilatura_pipeline(article_url, metadata_wanted)
        expected = 0
        message = ("get_article_metadata_trafilatura_pipeline(article_url, metadata_wanted) "
                   "returned {0} metadata, despite expecting {1}.".format(len(actual), expected))
        assert len(actual) == expected, message
        
    def test_get_article_url_and_metadata_title_date_url_description_trafilatura_pipeline_goodurl(self):
        homepage_url = "https://www.spiegel.de/"
        metadata_wanted = ['title', 'date', 'url', 'description']
        actual = get_article_urls_and_metadata_trafilatura_pipeline(homepage_url, metadata_wanted)
        not_expected = 0
        message = ("get_article_metadata_trafilatura_pipeline(article_url, metadata_wanted) "
                   "returned {0} articles with metadata.".format(len(actual)))
        assert len(actual) != not_expected, message        
        
    def test_get_article_url_and_metadata_title_date_url_description_trafilatura_pipeline_badurl(self):
        homepage_url = "https://smo-wiki.leibniz-hbi.de/"
        metadata_wanted = ['title', 'date', 'url', 'description']
        actual = get_article_urls_and_metadata_trafilatura_pipeline(homepage_url, metadata_wanted)
        expected = 0
        message = ("get_article_metadata_trafilatura_pipeline(article_url, metadata_wanted) "
                   "returned {0} articles with metadata, despite expecting {1}.".format(actual.shape[0],expected))
        assert actual.shape[0] == expected, message     

class TestFilterPipeline(object):
    ### Not sure if the first two make sense, as the trafilatura pipeline pipeline already 
    ### retrieves viable article URLs. 

    def test_filter_article_urls_trafilatura_pipeline_goodurl(self):
        homepage_url = "https://www.spiegel.de/"
        article_url_list = get_article_urls_trafilatura_pipeline(homepage_url)
        actual = filter_urls(article_url_list)
        not_expected = 0 
        message = ("filter_urls(article_url_list) "
                   "returned {0} filtered article URLs.".format(len(actual)))
        assert len(actual) != not_expected, message

    def test_filter_article_urls_trafilatura_pipeline_badurl(self):
        homepage_url = "https://www.badische-zeitung.de/"
        article_url_list = get_article_urls_trafilatura_pipeline(homepage_url)
        actual = filter_urls(article_url_list)
        expected = 0 
        message = ("filter_urls(article_url_list) "
                   "returned {0} filtered article URLs, despite expecting {1}.".format(len(actual),expected))
        assert len(actual) == expected, message    

    def test_filter_article_urls_bs_pipeline_goodurl(self):
        homepage_url = "https://www.badische-zeitung.de/"
        article_url_list = get_article_urls_bs_pipeline(homepage_url)
        actual = filter_urls(article_url_list)
        not_expected = 0 
        message = ("filter_urls(article_url_list) "
                   "returned {0} filtered article URLs.".format(len(actual)))
        assert len(actual) != not_expected, message

    def test_filter_get_article_url_and_metadata_title_date_url_description_trafilatura_pipeline_goodurl(self):
        homepage_url = "https://www.spiegel.de/"
        metadata_wanted = ['title', 'date', 'url', 'description']
        actual = get_filtered_article_urls_and_metadata_trafilatura_pipeline(homepage_url, metadata_wanted)
        not_expected = 0
        message = ("get_filtered_article_urls_and_metadata_trafilatura_pipeline(homepage_url, metadata_wanted) "
                   "returned {0} filtered articles with metadata.".format(actual.shape[0]))
        assert actual.shape[0] != not_expected, message      
        
    def test_filter_get_article_url_and_metadata_title_date_url_description_trafilatura_pipeline_badurl(self):
        homepage_url = "https://www.badische-zeitung.de/"
        metadata_wanted = ['title', 'date', 'url', 'description']
        actual = get_filtered_article_urls_and_metadata_trafilatura_pipeline(homepage_url, metadata_wanted)
        expected = 0
        message = ("get_filtered_article_urls_and_metadata_trafilatura_pipeline(homepage_url, metadata_wanted) "
                   "returned {0} filtered articles with metadata, despite expecting {1}.".format(actual.shape[0],expected))
        assert actual.shape[0] == expected, message     

    def test_filter_get_article_url_and_metadata_title_date_url_description_bs_pipeline_goodurl(self):
        homepage_url = "https://www.badische-zeitung.de/"
        metadata_wanted = ['title', 'date', 'url', 'description']
        actual = get_filtered_article_urls_and_metadata_bs_pipeline(homepage_url, metadata_wanted)
        not_expected = 0
        message = ("get_filtered_article_urls_and_metadata_bs_pipeline(homepage_url, metadata_wanted) "
                   "returned {0} filtered articles with metadata.".format(actual.shape[0]))
        assert actual.shape[0] != not_expected, message          

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
        metadata_wanted = ['title', 'date', 'url', 'description']
        actual = get_article_metadata_bs_pipeline(article_url, metadata_wanted)
        not_expected = 0
        message = ("get_article_metadata_bs_pipeline(article_url, metadata_wanted) "
                   "returned {0} metadata.".format(len(actual)))
        assert len(actual) != not_expected, message

    def test_get_article_metadata_complete_bs_pipeline(self):
        article_url = "https://www.badische-zeitung.de/unwetterwarnung-aufgehoben-aber-schnee-und-eis-sollen-ueber-nacht-zurueckkehren"
        metadata_wanted = "['title', 'author', 'url', 'hostname', 'description', 'sitename', 'date', 'categories', 'tags', 'fingerprint', 'id', 'license', 'body', 'comments', 'commentsbody', 'raw_text', 'text', 'language']"
        actual = get_article_metadata_bs_pipeline(article_url, metadata_wanted)
        not_expected = 0
        message = ("get_article_metadata_bs_pipeline(article_url, metadata_wanted) "
                   "returned {0} metadata.".format(len(actual)))
        assert len(actual) != not_expected, message

    def test_get_article_url_and_metadata_title_date_url_description_bs_pipeline_goodurl(self):
        homepage_url = "https://www.badische-zeitung.de/"
        metadata_wanted = ['title', 'date', 'url', 'description']
        actual = get_article_urls_and_metadata_bs_pipeline(homepage_url, metadata_wanted)
        not_expected = 0
        message = ("get_article_urls_and_metadata_bs_pipeline(article_url, metadata_wanted) "
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
        metadata_wanted = ['title', 'date', 'url', 'description']
        actual = get_pur_abo_article_urls_and_metadata(homepage_url, class_name, metadata_wanted)
        not_expected = 0
        message = ("get_pur_abo_article_urls_and_metadata(homepage_url, class_name) "
                   "returned {0} articles with metadata.".format(actual.shape[0]))
        assert actual.shape[0] != not_expected, message

    def get_pur_abo_filtered_article_urls_and_metadata(self):
        homepage_url = "https://www.zeit.de/"
        class_name = "sp_choice_type_11"
        metadata_wanted = ['title', 'date', 'url', 'description']
        actual = get_pur_abo_filtered_article_urls_and_metadata(homepage_url, class_name, metadata_wanted)
        not_expected = 0
        message = ("get_pur_abo_filtered_article_urls_and_metadata(homepage_url, class_name) "
                   "returned {0} filtered articles with metadata.".format(actual.shape[0]))
        assert actual.shape[0] != not_expected, message

class TestExportCSV(object):
    def test_export_trafilatura_pipeline_goodurl(self):
        homepage_url = "https://www.spiegel.de/"
        metadata_wanted = ['title', 'date', 'url', 'description']
        output_folder = "newsfeedback/output"
        df = get_filtered_article_urls_and_metadata_trafilatura_pipeline(homepage_url, metadata_wanted)
        df_path = export_dataframe(df, homepage_url, output_folder)
        df_from_file = pd.read_csv(df_path)
        message = ("The number of entries in the original dataframe ({0}) "
                   "is not identical to the number of entries "
                   "in the exported dataframe ({1}).".format(df.shape[0],df_from_file.shape[0]))                
        assert df.shape[0] == df_from_file.shape[0], message
    
    def test_export_bs_pipeline_goodurl(self):
        homepage_url = "https://www.badische-zeitung.de/"
        metadata_wanted = ['title', 'date', 'url', 'description']
        output_folder = "newsfeedback/output"
        df = get_filtered_article_urls_and_metadata_bs_pipeline(homepage_url, metadata_wanted)
        df_path = export_dataframe(df, homepage_url, output_folder)
        df_from_file = pd.read_csv(df_path)
        message = ("The number of entries in the original dataframe ({0}) "
                   "is not identical to the number of entries "
                   "in the exported dataframe ({1}).".format(df.shape[0],df_from_file.shape[0]))                
        assert df.shape[0] == df_from_file.shape[0], message

    def test_export_unfiltered_pur_abo(self):
        homepage_url = "https://www.zeit.de/"
        metadata_wanted = ['title', 'date', 'url', 'description']
        class_name = "sp_choice_type_11"
        output_folder = "newsfeedback/output"
        df = get_pur_abo_article_urls_and_metadata(homepage_url, class_name, metadata_wanted)
        df_path = export_dataframe(df, homepage_url, output_folder)
        df_from_file = pd.read_csv(df_path)
        message = ("The number of entries in the original dataframe ({0}) "
                   "is not identical to the number of entries "
                   "in the exported dataframe ({1}).".format(df.shape[0],df_from_file.shape[0]))                
        assert df.shape[0] == df_from_file.shape[0], message

    def test_export_filtered_pur_abo(self):
        homepage_url = "https://www.zeit.de/"
        metadata_wanted = ['title', 'date', 'url', 'description']
        class_name = "sp_choice_type_11"
        output_folder = "newsfeedback/output"
        df = get_pur_abo_filtered_article_urls_and_metadata(homepage_url, class_name, metadata_wanted)
        df_path = export_dataframe(df, homepage_url, output_folder)
        df_from_file = pd.read_csv(df_path)
        message = ("The number of entries in the original dataframe ({0}) "
                   "is not identical to the number of entries "
                   "in the exported dataframe ({1}).".format(df.shape[0],df_from_file.shape[0]))                
        assert df.shape[0] == df_from_file.shape[0], message

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
        message = ("get_metadata_trafilatura_pipeline(article_url, metadata_wanted) "
                   "returned no metadata.".format(caplog.text))
        assert "INFO" in caplog.text, message


    def test_click_get_article_metadata_title_date_url_description_trafilatura_pipeline_badurl(self, caplog):
        runner = CliRunner()
        article_url = "'https://hans-bredow-institut.de/'"
        runner.invoke(get_metadata_trafilatura_pipeline, f"-a {article_url} \n")
        message = ("get_metadata_trafilatura_pipeline(article_url, metadata_wanted) "
                   "returned metadata, despite none being expected.".format(caplog.text))
        assert "ERROR" in caplog.text, message    
    
    def test_click_get_both_goodurl(self, caplog):
        runner = CliRunner()
        homepage_url = "'https://www.spiegel.de/'"
        runner.invoke(get_both_trafilatura_pipeline, f"-u {homepage_url} \n")
        message = ("get_both_trafilatura_pipeline(homepage_url, metadata_wanted) "
                   "returned no articles with metadata.".format(caplog.text))
        assert "INFO" in caplog.text, message
        
    def test_click_get_both_badurl(self, caplog):
        runner = CliRunner()
        homepage_url = "'https://smo-wiki.leibniz-hbi.de/'"
        runner.invoke(get_both_trafilatura_pipeline, f"-u {homepage_url} \n")
        message = ("get_both_trafilatura_pipeline(homepage_url, metadata_wanted) "
                   "returned articles with metadata, despite none being expected.".format(caplog.text))
        assert "ERROR" in caplog.text, message

class TestClickbs_pipeline(object):
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
        message = ("get_metadata_bs_pipeline(article_url, metadata_wanted) "
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
        message = ("filter_both_trafilatura_pipeline(homepage_url, metadata_wanted) "
                   "removed no articles.".format(caplog.text))
        assert "INFO" in caplog.text, message

    def test_filter_both_trafilatura_pipeline_badurl(self, caplog):
        runner = CliRunner()
        homepage_url = "'https://www.badische-zeitung.de/'"
        runner.invoke(filter_both_trafilatura_pipeline, f"-u {homepage_url} \n")
        message = ("filter_both_trafilatura_pipeline(homepage_url, metadata_wanted) "
                   "returned articles, despite none being expected.".format(caplog.text))
        assert "ERROR" in caplog.text, message

    def test_filter_both_bs_pipeline_goodurl(self, caplog):
        runner = CliRunner()
        homepage_url = "'https://www.badische-zeitung.de/'"
        runner.invoke(filter_both_bs_pipeline, f"-u {homepage_url} \n")
        message = ("filter_both_bs_pipeline(homepage_url, metadata_wanted) "
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

