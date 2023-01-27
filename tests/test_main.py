""" Test suite for newsfeedback.main
"""
import pytest, sys
import pandas as pd
from click.testing import CliRunner
from _pytest.logging import LogCaptureFixture
from loguru import logger as log
from newsfeedback.main import get_article_urls_best_case, get_article_metadata_best_case, get_article_urls_and_metadata_best_case
from newsfeedback.main import get_article_urls_worst_case, get_article_metadata_worst_case, get_article_urls_and_metadata_worst_case
from newsfeedback.main import filter_urls, get_filtered_article_urls_and_metadata_best_case, get_filtered_article_urls_and_metadata_worst_case
from newsfeedback.main import export_dataframe
from newsfeedback.main import accept_pur_abo_homepage, accept_pur_abo_article, get_pur_abo_article_urls, get_pur_abo_article_urls_and_metadata, get_pur_abo_filtered_article_urls_and_metadata
from newsfeedback.main import get_articles_bestcase, get_metadata_bestcase, get_both_bestcase
from newsfeedback.main import get_articles_worstcase,  get_metadata_worstcase, get_both_worstcase
from newsfeedback.main import filter_articles, filter_both_bestcase, filter_both_worstcase
from newsfeedback.main import consent_button_homepage, consent_button_article, consent_articles, consent_both, filter_consent_both

@pytest.fixture
def caplog(caplog: LogCaptureFixture):
    handler_id = log.add(caplog.handler)
    yield caplog
    log.remove(handler_id)

class TestBestCasePipeline(object):
    def test_get_article_urls_bestcase_goodurl(self):
        """ Asserts whether article URLs have successfully been extracted from a "best case" homepage.
        """
        homepage_url = "https://www.spiegel.de/"
        actual = get_article_urls_best_case(homepage_url)
        not_expected = 0
        message = ("get_article_urls_best_case(homepage_url) "
                   "returned {0}, which is identical "
                   "to {1}".format(len(actual),not_expected))
        assert len(actual) != not_expected, message
        
    def test_get_article_urls_bestcase_badurl(self):
        """ Asserts whether article URLs fail to be extracted from a "worst case" homepage.
        """
        homepage_url = "https://www.badische-zeitung.de/"
        actual = get_article_urls_best_case(homepage_url)
        expected = 0
        message = ("get_article_urls_best_case(homepage_url) "
                   "returned {0} instead "
                   "of {1}".format(len(actual),expected))
        assert len(actual) == expected, message
    
    def test_get_article_metadata_title_date_url_description_bestcase_goodurl(self):
        """ Asserts whether the desired metadata (in this case: Title, Date, URL, Description) 
        can be extracted from an article
        """
        article_url = "https://www.spiegel.de/netzwelt/apps/elon-musk-hetzt-auf-twitter-gegen-anthony-fauci-und-die-queere-community-und-wird-ausgebuht-a-edd3c470-12cb-485d-a6f9-266dc94279de"
        metadata_wanted = ['title', 'date', 'url', 'description']
        actual = get_article_metadata_best_case(article_url, metadata_wanted)
        not_expected = 0
        message = ("get_article_metadata_best_case(article_url, metadata_wanted) "
                   "returned {0}, which is identical "
                   "to {1}".format(len(actual),not_expected))
        assert len(actual) != not_expected, message
       
    def test_get_article_metadata_title_date_url_description_bestcase_badurl(self):        
        """ Asserts whether the desired metadata (in this case: Title, Date, URL, Description) 
        fail to be extracted from a webpage that is not an article
        """
        article_url = "https://hans-bredow-institut.de/"
        metadata_wanted = ['title', 'date', 'url', 'description']
        actual = get_article_metadata_best_case(article_url, metadata_wanted)
        expected = 0
        message = ("get_article_metadata_best_case(article_url, metadata_wanted) "
                   "returned {0} instead "
                   "of {1}".format(len(actual),expected))
        assert len(actual) == expected, message
        
    def test_get_article_url_and_metadata_title_date_url_description_bestcase_goodurl(self):
        """ Asserts whether the desired metadata (in this case: Title, Date, URL, Description) 
        can be extracted from an article whose URL was previously extracted from a "best case" homepage
        """
        homepage_url = "https://www.spiegel.de/"
        metadata_wanted = ['title', 'date', 'url', 'description']
        actual = get_article_urls_and_metadata_best_case(homepage_url, metadata_wanted)
        not_expected = 0
        message = ("get_article_metadata_best_case(article_url, metadata_wanted) "
                   "returned {0}, which is identical "
                   "to {1}".format(len(actual),not_expected))
        assert len(actual) != not_expected, message        
        
    def test_get_article_url_and_metadata_title_date_url_description_bestcase_badurl(self):
        """ Asserts whether the desired metadata (in this case: Title, Date, URL, Description) 
        fail to be extracted from a URL that is not an article and thus a "bad URL" within the
        "best case" pipeline.
        """
        homepage_url = "https://smo-wiki.leibniz-hbi.de/"
        metadata_wanted = ['title', 'date', 'url', 'description']
        actual = get_article_urls_and_metadata_best_case(homepage_url, metadata_wanted)
        expected = 0
        message = ("get_article_metadata_best_case(article_url, metadata_wanted) "
                   "returned {0}, instead "
                   "of {1}".format(actual.shape[0],expected))
        assert actual.shape[0] == expected, message     

class TestFilterPipeline(object):
    ### Not sure if the first two make sense, as the best case pipeline already 
    ### retrieves viable article URLs. 

    def test_filter_article_urls_bestcase_goodurl(self):
        """ Asserts whether article URLs extracted with
        trafilatura remain following the filtering process.
        """
        homepage_url = "https://www.spiegel.de/"
        article_url_list = get_article_urls_best_case(homepage_url)
        #article_url_list = get_article_urls_best_case.article_url_list
        actual = filter_urls(article_url_list)
        not_expected = 0 
        message = ("filter_urls(article_url_list) "
                   "returned {0}, which is identical "
                   "to {1}".format(len(actual),not_expected))
        assert len(actual) != not_expected, message

    def test_filter_article_urls_bestcase_badurl(self):
        """ Asserts whether article URLs continue to fail to be extracted and subsequently
        fail to be filtered when using a "bad" URL.
        """
        homepage_url = "https://www.badische-zeitung.de/"
        article_url_list = get_article_urls_best_case(homepage_url)
        #article_url_list = get_article_urls_best_case.article_url_list
        actual = filter_urls(article_url_list)
        expected = 0 
        message = ("filter_urls(article_url_list) "
                   "returned {0} instead "
                   "of {1}".format(len(actual),expected))
        assert len(actual) == expected, message    

    def test_filter_article_urls_worstcase_goodurl(self):
        """ Asserts whether article URLs extracted with
        beautifulsoup remain following the filtering process.
        """
        homepage_url = "https://www.badische-zeitung.de/"
        article_url_list = get_article_urls_worst_case(homepage_url)
        #article_url_list = get_article_urls_worst_case.article_url_list
        actual = filter_urls(article_url_list)
        not_expected = 0 
        message = ("filter_urls(article_url_list) "
                   "returned {0}, which is identical "
                   "to {1}".format(len(actual),not_expected))
        assert len(actual) != not_expected, message

    def test_filter_get_article_url_and_metadata_title_date_url_description_bestcase_goodurl(self):
        """ Asserts whether the desired metadata (in this case: Title, Date, URL, Description) 
        can be extracted from a "best case" homepage article which remained after the filtering process.
        """
        homepage_url = "https://www.spiegel.de/"
        metadata_wanted = ['title', 'date', 'url', 'description']
        actual = get_filtered_article_urls_and_metadata_best_case(homepage_url, metadata_wanted)
        not_expected = 0
        message = ("get_filtered_article_urls_and_metadata_best_case(article_url, metadata_wanted) "
                   "returned {0}, which is identical "
                   "to {1}".format(actual.shape[0],not_expected))
        assert actual.shape[0] != not_expected, message        
        
    def test_filter_get_article_url_and_metadata_title_date_url_description_bestcase_badurl(self):
        """ Asserts whether the desired metadata (in this case: Title, Date, URL, Description) 
        fail to be extracted from a URL that is not an article. It is thus a "bad URL" within the
        "best case" filtered URL pipeline.
        """
        homepage_url = "https://www.badische-zeitung.de/"
        metadata_wanted = ['title', 'date', 'url', 'description']
        actual = get_filtered_article_urls_and_metadata_best_case(homepage_url, metadata_wanted)
        expected = 0
        message = ("get_filtered_article_urls_and_metadata_best_case(article_url, metadata_wanted) "
                   "returned {0}, instead "
                   "of {1}".format(actual.shape[0],expected))
        assert actual.shape[0] == expected, message     

    def test_filter_get_article_url_and_metadata_title_date_url_description_worstcase_goodurl(self):
        """ Asserts whether the article URLs and desired metadata (in this case: Title, Date, URL, Description) 
        can be extracted from "worst case" homepage articles which remained after the filtering process.
        """
        homepage_url = "https://www.badische-zeitung.de/"
        metadata_wanted = ['title', 'date', 'url', 'description']
        actual = get_filtered_article_urls_and_metadata_worst_case(homepage_url, metadata_wanted)
        not_expected = 0
        message = ("get_filtered_article_urls_and_metadata_worst_case(article_url, metadata_wanted) "
                   "returned {0}, which is identical "
                   "to {1}".format(actual.shape[0],not_expected))
        assert actual.shape[0] != not_expected, message          

class TestWorstCasePipeline(object):
    def test_get_article_urls_worstcase_goodurl(self):
        """ Asserts whether article URLs have successfully been extracted from a "worst case" homepage
        using beautifulsoup.
        """
        homepage_url = "https://www.badische-zeitung.de/"
        actual = get_article_urls_worst_case(homepage_url)
        not_expected = 0
        message = ("get_article_urls_worst_case(homepage_url) "
                   "returned {0}, which is identical "
                   "to {1}".format(len(actual),not_expected))
        assert len(actual) != not_expected, message

    ### would be good to find an URL without any a hrefs to test the opposing case

    def test_get_article_metadata_title_date_url_description_worstcase_goodurl(self):
        """ Asserts whether the desired metadata (in this case: Title, Date, URL, Description) 
        can be extracted from an article URL that was retrieved from the homepage whose articles
        can only be extracted with beautifulsoup.
        """
        article_url = "https://www.badische-zeitung.de/unwetterwarnung-aufgehoben-aber-schnee-und-eis-sollen-ueber-nacht-zurueckkehren"
        metadata_wanted = ['title', 'date', 'url', 'description']
        actual = get_article_metadata_worst_case(article_url, metadata_wanted)
        not_expected = 0
        message = ("get_article_metadata_worst_case(article_url, metadata_wanted) "
                   "returned {0}, which is identical "
                   "to {1}".format(len(actual),not_expected))
        assert len(actual) != not_expected, message

    def test_get_article_url_and_metadata_title_date_url_description_worstcase_goodurl(self):
        """ Asserts whether the article URLs and desired metadata (in this case: Title, Date, URL, Description) 
        can be extracted from a "worst case" homepage.
        """
        homepage_url = "https://www.badische-zeitung.de/"
        metadata_wanted = ['title', 'date', 'url', 'description']
        actual = get_article_urls_and_metadata_worst_case(homepage_url, metadata_wanted)
        not_expected = 0
        message = ("get_article_urls_and_metadata_worst_case(article_url, metadata_wanted) "
                   "returned {0}, which is identical "
                   "to {1}".format(actual.shape[0],not_expected))
        assert actual.shape[0] != not_expected, message          

class TestWebsiteSpecificFunctions(object):
    def test_accept_pur_abo_consent_button(self):
        """ Asserts whether the elements (iframe, button and homepage title) were found by printing
        out the page source of the homepage.
        """
        homepage_url = "https://www.zeit.de/"
        class_name = "sp_choice_type_11" # full class names: 'message-component message-button no-children focusable sp_choice_type_11'
        homepage_title = "ZEIT ONLINE | Nachrichten, News, Hintergründe und Debatten"
        actual = accept_pur_abo_homepage(homepage_url, class_name)
        driver = actual[1]
        #driver = accept_pur_abo_homepage.driver
        driver.quit()
        error_message = 'Element could not be found, connection timed out.'
        message = ("accept_pur_abo(homepage_url, class_name) "
                  "returned {0}, which is an undesired error message.".format(actual[0], error_message))
        assert actual[0] != error_message, message    
        
    def test_accept_pur_abo_subscription_button(self):
        """ Checks that a TimeOutException has occurred by asserting whether the
        desired error message has been printed.
        """
        homepage_url = "https://www.zeit.de/"
        class_name = "js-forward-link-purabo" # full class names: 'option__button option__button--pur js-forward-link-purabo'
        actual = accept_pur_abo_homepage(homepage_url, class_name)
        driver = actual[1]
        #driver = accept_pur_abo_homepage.driver
        driver.quit()
        error_message = 'Element could not be found, connection timed out.'
        message = ("accept_pur_abo(homepage_url, class_name) did not return "
                   "the desired error message, but instead"
                   "{0}".format(actual[0], error_message))
        assert actual[0] == error_message, message   
    
    def test_accept_pur_abo_article_consent_button(self):
        """ Asserts whether the elements (iframe, button and homepage title) were found by printing
        out the page source of the article.
        """
        article_url_list = ["https://www.zeit.de/zett/politik/2022-12/mihran-dabag-voelkermord-jesiden-bundestag-kriegsgewalt", "https://www.zeit.de/gesellschaft/zeitgeschehen/2023-01/illerkirchberg-mord-buergerdialog-ece-s-vater"]
        class_name = "sp_choice_type_11" # full class names: 'message-component message-button no-children focusable sp_choice_type_11'
        actual = accept_pur_abo_article(article_url_list, class_name)
        #driver = accept_pur_abo_article.driver
        driver = actual[1]
        driver.quit()
        error_message = 'Element could not be found, connection timed out.'
        message = ("accept_pur_abo(homepage_url, class_name) "
                  "returned {0}, which is an undesired error message.".format(actual[0], error_message))
        assert actual[0] != error_message, message 

    def test_get_pur_abo_article_urls(self):
        """ Asserts that article URLs are returned after the consent button
        has been clicked.
        """
        homepage_url = "https://www.zeit.de/"
        class_name = "sp_choice_type_11"
        actual = get_pur_abo_article_urls(homepage_url, class_name)
        not_expected = 0
        message = ("get_pur_abo_article_urls(homepage_url, class_name) "
                   "returned {0}, which is identical "
                   "to {1}".format(len(actual),not_expected))
        assert len(actual) != not_expected, message

    def test_get_pur_abo_article_urls_and_metadata(self):
        """ Asserts that article URLs and metadata are returned after the consent
        buttons for both the homepage and the first article page have been clicked.
        """
        homepage_url = "https://www.zeit.de/"
        class_name = "sp_choice_type_11"
        metadata_wanted = ['title', 'date', 'url', 'description']
        actual = get_pur_abo_article_urls_and_metadata(homepage_url, class_name, metadata_wanted)
        #driver = get_pur_abo_article_urls_and_metadata.driver
        #driver.quit()
        not_expected = 0
        message = ("get_pur_abo_article_urls_and_metadata(homepage_url, class_name) "
                   "returned {0}, which is identical "
                   "to {1}".format(actual.shape[0],not_expected))
        assert actual.shape[0] != not_expected, message

    def get_pur_abo_filtered_article_urls_and_metadata(self):
        """ Asserts that article URLs and metadata are returned after the consent
        buttons for both the homepage and the first article page have been clicked.
        Articles are filtered prior to metadata extraction.
        """
        homepage_url = "https://www.zeit.de/"
        class_name = "sp_choice_type_11"
        metadata_wanted = ['title', 'date', 'url', 'description']
        actual = get_pur_abo_filtered_article_urls_and_metadata(homepage_url, class_name, metadata_wanted)
        #driver = get_pur_abo_filtered_article_urls_and_metadata.driver
        #driver.quit()
        not_expected = 0
        message = ("get_pur_abo_filtered_article_urls_and_metadata(homepage_url, class_name) "
                   "returned {0}, which is identical "
                   "to {1}".format(actual.shape[0],not_expected))
        assert actual.shape[0] != not_expected, message

class TestExportCSV(object):
    def test_export_bestcase_goodurl(self):
        """ Asserts that the dataframe put into the export function and the final
        CSV are the same length. The data for the dataframe has gone through the best case pipeline.
        """
        homepage_url = "https://www.spiegel.de/"
        metadata_wanted = ['title', 'date', 'url', 'description']
        output_folder = "newsfeedback/output"
        df = get_filtered_article_urls_and_metadata_best_case(homepage_url, metadata_wanted)
        df_path = export_dataframe(df, homepage_url, output_folder)
        #df_path = export_dataframe.df_path
        df_from_file = pd.read_csv(df_path)
        message = ("The number of entries in the original dataframe ({0}) "
                   "is not identical to the number of entries "
                   "in the exported dataframe ({1}).".format(df.shape[0],df_from_file.shape[0]))                
        assert df.shape[0] == df_from_file.shape[0], message
    
    def test_export_worstcase_goodurl(self):
        """ Asserts that the dataframe put into the export function and the final
        CSV are the same length. The data for the dataframe has gone through the worst case pipeline.
        """
        homepage_url = "https://www.badische-zeitung.de/"
        metadata_wanted = ['title', 'date', 'url', 'description']
        output_folder = "newsfeedback/output"
        df = get_filtered_article_urls_and_metadata_worst_case(homepage_url, metadata_wanted)
        df_path = export_dataframe(df, homepage_url, output_folder)
        #df_path = export_dataframe.df_path
        df_from_file = pd.read_csv(df_path)
        message = ("The number of entries in the original dataframe ({0}) "
                   "is not identical to the number of entries "
                   "in the exported dataframe ({1}).".format(df.shape[0],df_from_file.shape[0]))                
        assert df.shape[0] == df_from_file.shape[0], message

    def test_export_unfiltered_pur_abo(self):
        """ Asserts that the dataframe put into the export function and the final
        CSV are the same length. The data for the dataframe has been extracted from a 
        site that has a consent button.
        """
        homepage_url = "https://www.zeit.de/"
        metadata_wanted = ['title', 'date', 'url', 'description']
        class_name = "sp_choice_type_11"
        output_folder = "newsfeedback/output"
        df = get_pur_abo_article_urls_and_metadata(homepage_url, class_name, metadata_wanted)
        df_path = export_dataframe(df, homepage_url, output_folder)
        # df_path = export_dataframe.df_path
        df_from_file = pd.read_csv(df_path)
        message = ("The number of entries in the original dataframe ({0}) "
                   "is not identical to the number of entries "
                   "in the exported dataframe ({1}).".format(df.shape[0],df_from_file.shape[0]))                
        assert df.shape[0] == df_from_file.shape[0], message

    def test_export_filtered_pur_abo(self):
        """ Asserts that the dataframe put into the export function and the final
        CSV are the same length. The data for the dataframe has been extracted from a 
        site that has a consent button. Furthermore, the data is filtered.
        """
        homepage_url = "https://www.zeit.de/"
        metadata_wanted = ['title', 'date', 'url', 'description']
        class_name = "sp_choice_type_11"
        output_folder = "newsfeedback/output"
        df = get_pur_abo_filtered_article_urls_and_metadata(homepage_url, class_name, metadata_wanted)
        df_path = export_dataframe(df, homepage_url, output_folder)
        #df_path = export_dataframe.df_path
        df_from_file = pd.read_csv(df_path)
        message = ("The number of entries in the original dataframe ({0}) "
                   "is not identical to the number of entries "
                   "in the exported dataframe ({1}).".format(df.shape[0],df_from_file.shape[0]))                
        assert df.shape[0] == df_from_file.shape[0], message

class TestClickBestCase(object):
    def test_click_get_articles_bestcase_goodurl(self, caplog):
        """ Asserts whether article URLs have successfully been extracted from a "best case" homepage.
        """
        runner = CliRunner()
        homepage_url = "'https://www.spiegel.de/'"
        runner.invoke(get_articles_bestcase, f"-u {homepage_url} \n")
        message = ("get_articles_bestcase(homepage_url) "
                   "returned no articles.".format(caplog.text))
        #assert len(actual) != not_expected, message
        assert "INFO" in caplog.text, message

    def test_click_get_articles_bestcase_badurl(self, caplog):
        """ Asserts whether article URLs fail to be extracted from a "worst case" homepage.
        """
        runner = CliRunner()
        homepage_url = "'https://www.badische-zeitung.de/'"
        runner.invoke(get_articles_bestcase, f"-u {homepage_url} \n")
        message = ("with_click_get_article_urls_best_case(homepage_url) "
                   "returned articles from a bad URL.".format(caplog.text))
        #assert len(actual) != not_expected, message
        assert "ERROR" in caplog.text, message

    def test_click_get_article_metadata_title_date_url_description_bestcase_goodurl(self, caplog):
        """ Asserts whether the desired metadata (in this case: Title, Date, URL, Description) 
        can be extracted from an article
        """
        runner = CliRunner()
        article_url = "'https://www.spiegel.de/netzwelt/apps/elon-musk-hetzt-auf-twitter-gegen-anthony-fauci-und-die-queere-community-und-wird-ausgebuht-a-edd3c470-12cb-485d-a6f9-266dc94279de'"
        runner.invoke(get_metadata_bestcase, f"-a {article_url} \n")
        message = ("get_metadata_bestcase(article_url, metadata_wanted) "
                   "returned no metadata.".format(caplog.text))
        assert "INFO" in caplog.text, message

    def test_click_get_article_metadata_title_date_url_description_bestcase_badurl(self, caplog):
        """ Asserts whether the desired metadata (in this case: Title, Date, URL, Description) 
        fail to be extracted from a webpage that is not an article
        """
        runner = CliRunner()
        article_url = "'https://hans-bredow-institut.de/'"
        runner.invoke(get_metadata_bestcase, f"-a {article_url} \n")
        message = ("get_metadata_bestcase(article_url, metadata_wanted) "
                   "returned metadata from a nonviable URL.".format(caplog.text))
        assert "ERROR" in caplog.text, message    
    
    def test_click_get_both_goodurl(self, caplog):
        """ Asserts whether the desired metadata (in this case: Title, Date, URL, Description) 
        can be extracted from an article whose URL was previously extracted from a "best case" homepage
        """
        runner = CliRunner()
        homepage_url = "'https://www.spiegel.de/'"
        runner.invoke(get_both_bestcase, f"-u {homepage_url} \n")
        message = ("get_both_bestcase(homepage_url, metadata_wanted) "
                   "returned no articles with metadata.".format(caplog.text))
        assert "INFO" in caplog.text, message
        
    def test_click_get_both_badurl(self, caplog):
        """
        """
        runner = CliRunner()
        homepage_url = "'https://smo-wiki.leibniz-hbi.de/'"
        runner.invoke(get_both_bestcase, f"-u {homepage_url} \n")
        message = ("get_both_bestcase(homepage_url, metadata_wanted) "
                   "returned articles with metadata from a nonviable URL.".format(caplog.text))
        assert "ERROR" in caplog.text, message

class TestClickWorstCase(object):
    def test_click_get_articles_worstcase_goodurl(self, caplog):
        """
        """
        runner = CliRunner()
        homepage_url = "'https://www.badische-zeitung.de/'"
        runner.invoke(get_articles_worstcase, f"-u {homepage_url} \n")
        message = ("get_articles_worstcase(homepage_url) "
                   "returned no articles.".format(caplog.text))
        #assert len(actual) != not_expected, message
        assert "INFO" in caplog.text, message

    def test_click_get_article_metadata_title_date_url_description_worstcase_goodurl(self, caplog):
        """
        """
        runner = CliRunner()
        article_url = "'https://www.badische-zeitung.de/unwetterwarnung-aufgehoben-aber-schnee-und-eis-sollen-ueber-nacht-zurueckkehren'"
        runner.invoke(get_metadata_worstcase, f"-a {article_url} \n")
        message = ("get_metadata_worstcase(article_url, metadata_wanted) "
                   "returned no metadata.".format(caplog.text))
        assert "INFO" in caplog.text, message

    def test_click_get_both_worstcase_goodurl(self, caplog):
        runner = CliRunner()
        homepage_url = "'https://www.badische-zeitung.de/'"
        runner.invoke(get_both_worstcase, f"-u {homepage_url} \n")
        message = ("get_both_worstcase(homepage_url) "
                   "returned no articles with metadata.".format(caplog.text))
        #assert len(actual) != not_expected, message
        assert "INFO" in caplog.text, message

class TestClickFilter(object):
    def test_filter_urls(self, caplog):
        """
        """
        runner = CliRunner()
        homepage_url = "'https://www.badische-zeitung.de/'"
        runner.invoke(filter_articles, f"-u {homepage_url} \n")
        message = ("filter_articles(homepage_url) "
                   "removed no articles.".format(caplog.text))
        #assert len(actual) != not_expected, message
        assert "INFO" in caplog.text, message
    
    def test_filter_both_bestcase_goodurl(self, caplog):
        """
        """
        runner = CliRunner()
        homepage_url = "'https://www.spiegel.de/'"
        runner.invoke(filter_both_bestcase, f"-u {homepage_url} \n")
        message = ("filter_both_bestcase(homepage_url, metadata_wanted) "
                   "removed no articles.".format(caplog.text))
        #assert len(actual) != not_expected, message
        assert "INFO" in caplog.text, message

    def test_filter_both_bestcase_badurl(self, caplog):
        """
        """
        runner = CliRunner()
        homepage_url = "'https://www.badische-zeitung.de/'"
        runner.invoke(filter_both_bestcase, f"-u {homepage_url} \n")
        message = ("filter_both_bestcase(homepage_url, metadata_wanted) "
                   "found viable articles from an unviable homepage.".format(caplog.text))
        #assert len(actual) != not_expected, message
        assert "ERROR" in caplog.text, message

    def test_filter_both_worstcase_goodurl(self, caplog):
        """
        """
        runner = CliRunner()
        homepage_url = "'https://www.badische-zeitung.de/'"
        runner.invoke(filter_both_worstcase, f"-u {homepage_url} \n")
        message = ("filter_both_worstcase(homepage_url, metadata_wanted) "
                   "removed no articles.".format(caplog.text))
        #assert len(actual) != not_expected, message
        assert "INFO" in caplog.text, message

    class TestClickSiteSpecific(object):
        def test_consent_button_homepage(self, caplog):
            """
            """
            runner = CliRunner()
            homepage_url = "'https://www.zeit.de/'"
            runner.invoke(consent_button_homepage, f"-u {homepage_url} \n")
            message = ("consent_button_homepage(homepage_url, class_name) "
                       "was unable to click the consent button "
                       "on the given homepage. ".format(caplog.text))
            assert "INFO" in caplog.text, message
        
        def test_subscription_button_homepage(self, caplog):
            """
            """
            runner = CliRunner()
            homepage_url = "'https://www.zeit.de/'"
            class_name = "js-forward-link-purabo"
            runner.invoke(consent_button_homepage, f"-u {homepage_url} -c {class_name}\n")
            message = ("consent_button_homepage(homepage_url, class_name) "
                       "was unable to click the subscription button "
                       "on the given homepage. ".format(caplog.text))
            assert "ERROR" in caplog.text, message

        def test_consent_articles(self, caplog):
            """
            """
            runner = CliRunner()
            homepage_url = "'https://www.zeit.de/'"
            runner.invoke(consent_articles, f"-u {homepage_url} \n")
            message = (" ".format(caplog.text)) 
            assert "INFO" in caplog.text, message

        def test_consent_both(self, caplog):
            """
            """
            runner = CliRunner()
            homepage_url = "'https://www.zeit.de/'"
            runner.invoke(consent_both, f"-u {homepage_url} \n")
            message = (" ".format(caplog.text))
            assert "INFO" in caplog.text, message

        def test_filter_consent_both(self, caplog):
            """
            """
            runner = CliRunner()
            homepage_url = "'https://www.zeit.de/'"
            runner.invoke(filter_consent_both, f"-u {homepage_url} \n")
            message = (" ".format(caplog.text))
            assert "INFO" in caplog.text, message

