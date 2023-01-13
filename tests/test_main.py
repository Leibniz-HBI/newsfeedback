""" Test suite for newsfeedback.main
"""
import pytest
import pandas as pd
from newsfeedback.main import get_article_urls_best_case, get_article_metadata_best_case, get_article_urls_and_metadata_best_case
from newsfeedback.main import get_article_urls_worst_case, get_article_metadata_worst_case, get_article_urls_and_metadata_worst_case
from newsfeedback.main import filter_urls, get_filtered_article_urls_and_metadata_best_case, get_filtered_article_urls_and_metadata_worst_case, export_dataframe
from newsfeedback.main import accept_pur_abo

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
    def test_filter_article_urls_bestcase_goodurl(self):
        """ Asserts whether article URLs extracted with
        trafilatura remain following the filtering process.
        """
        homepage_url = "https://www.spiegel.de/"
        get_article_urls_best_case(homepage_url)
        article_url_list = get_article_urls_best_case.article_url_list
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
        get_article_urls_best_case(homepage_url)
        article_url_list = get_article_urls_best_case.article_url_list
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
        get_article_urls_worst_case(homepage_url)
        article_url_list = get_article_urls_worst_case.article_url_list
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
        actual = accept_pur_abo(homepage_url, class_name)
        error_message = 'Element could not be found, connection timed out.'
        message = ("accept_pur_abo(homepage_url, class_name) "
                  "returned {0}, which is an undesired error message.".format(actual, error_message))
        assert actual != error_message, message    
        
    def test_accept_pur_abo_subscription_button(self):
        """ Checks that a TimeOutException has occurred by asserting whether the
        desired error message has been printed.
        """
        homepage_url = "https://www.zeit.de/"
        class_name = "js-forward-link-purabo" # full class names: 'option__button option__button--pur js-forward-link-purabo'
        actual = accept_pur_abo(homepage_url, class_name)
        error_message = 'Element could not be found, connection timed out.'
        message = ("accept_pur_abo(homepage_url, class_name) did not return "
                   "the desired error message, but instead"
                   "{0}".format(actual, error_message))
        assert actual == error_message, message   

class TestExportCSV(object):
    def test_export_bestcase_goodurl(self):
        """ Asserts whether the dataframe put into the export function and the final
        CSV are the same length. The data for the dataframe has gone through the best case pipeline.
        """
        homepage_url = "https://www.spiegel.de/"
        metadata_wanted = ['title', 'date', 'url', 'description']
        output_folder = "newsfeedback/output"
        df = get_filtered_article_urls_and_metadata_best_case(homepage_url, metadata_wanted)
        export_dataframe(df, homepage_url, output_folder)
        df_path = export_dataframe.df_path
        df_from_file = pd.read_csv(df_path)
        message = ("The number of entries in the original dataframe ({0}) "
                   "is not identical to the number of entries "
                   "in the exported dataframe ({1}).".format(df.shape[0],df_from_file.shape[0]))                
        assert df.shape[0] == df_from_file.shape[0], message
    
    def test_export_worstcase_goodurl(self):
        """ Asserts whether the dataframe put into the export function and the final
        CSV are the same length. The data for the dataframe has gone through the worst case pipeline.
        """
        homepage_url = "https://www.badische-zeitung.de/"
        metadata_wanted = ['title', 'date', 'url', 'description']
        output_folder = "newsfeedback/output"
        df = get_filtered_article_urls_and_metadata_worst_case(homepage_url, metadata_wanted)
        export_dataframe(df, homepage_url, output_folder)
        df_path = export_dataframe.df_path
        df_from_file = pd.read_csv(df_path)
        message = ("The number of entries in the original dataframe ({0}) "
                   "is not identical to the number of entries "
                   "in the exported dataframe ({1}).".format(df.shape[0],df_from_file.shape[0]))                
        assert df.shape[0] == df_from_file.shape[0], message
