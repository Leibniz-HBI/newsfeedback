""" Test suite for newsfeedback.main
"""

import pytest

from newsfeedback.main import cli_implementation, get_article_urls_best_case

@pytest.mark.parametrize("name,expectation",[("World", "Hello World!")])
def test_cli(name: str, expectation: str) -> None:
    """ Asserts whether greetings are correct.
    """
    assert cli_implementation(name) == expectation
    
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
    
    