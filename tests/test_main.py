""" Test suite for newsfeedback.main
"""

import pytest

from newsfeedback.main import cli_implementation, get_article_urls_best_case, get_article_metadata_best_case, get_article_urls_and_metadata_best_case
   
class TestBestCasePipeline(object):
    def test_GetArticleURLs_BestCase_GoodURL(self):
        """ Asserts whether article URLs have successfully been extracted from a "best case" homepage.
        """
        homepage_url = "https://www.spiegel.de/"
        actual = get_article_urls_best_case(homepage_url)
        not_expected = 0
        message = ("get_article_urls_best_case(homepage_url) "
                   "returned {0}, which is identical "
                   "to {1}".format(len(actual),not_expected))
        assert len(actual) != not_expected, message
        
    def test_GetArticleURLs_BestCase_BadURL(self):
        """ Asserts whether article URLs fail to be extracted from a "worst case" homepage.
        """
        homepage_url = "https://www.badische-zeitung.de/"
        actual = get_article_urls_best_case(homepage_url)
        expected = 0
        message = ("get_article_urls_best_case(homepage_url) "
                   "returned {0} instead "
                   "of {1}".format(len(actual),expected))
        assert len(actual) == expected, message
     
    def test_GetArticleMetadata_TitleDateURLDescription_BestCase_GoodURL(self):
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
       
    def test_GetArticleMetadata_TitleDateURLDescription_BestCase_BadURL(self):        
        """ Asserts whether the desired metadata (in this case: Title, Date, URL, Description) 
        fail to be extracted from a webpage that is not an article
        """
        article_url = "https://leibniz-hbi.de/en"
        metadata_wanted = ['title', 'date', 'url', 'description']
        actual = get_article_metadata_best_case(article_url, metadata_wanted)
        expected = 0
        message = ("get_article_metadata_best_case(article_url, metadata_wanted) "
                   "returned {0} instead "
                   "of {1}".format(len(actual),expected))
        assert len(actual) == expected, message
        
    def test_GetArticleURLAndMetadata_TitleDateURLDescription_BestCase_GoodURL(self):
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
        
    def test_GetArticleURLAndMetadata_TitleDateURLDescription_BestCase_BadURL(self):
        """ Asserts whether the desired metadata (in this case: Title, Date, URL, Description) 
        fail to be extracted from an article whose URL failed to be extracted from a "worst case" homepage
        """
        homepage_url = "https://leibniz-hbi.de/en"
        metadata_wanted = ['title', 'date', 'url', 'description']
        actual = get_article_urls_and_metadata_best_case(homepage_url, metadata_wanted)
        expected = 0
        message = ("get_article_metadata_best_case(article_url, metadata_wanted) "
                   "returned {0}, instead "
                   "of {1}".format(len(actual),expected))
        assert len(actual) == expected, message        
        
