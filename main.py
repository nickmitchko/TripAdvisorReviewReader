from pyquery import PyQuery

from lxml import etree

import urllib

baseUrl = "https://www.tripadvisor.com/"

html1 = PyQuery(url='https://www.tripadvisor.com/Search?q=dance+classes&geo=60763&pid=3826&typeaheadRedirect=true&redirect=&startTime=1460253914937&uiOrigin=MASTHEAD&returnTo=__2F__&searchSessionId=405A7735978BFCBB83D06026999065331460239467712ssid#&ssrc=A&o=0')
html2 = PyQuery(url='https://www.tripadvisor.com/Search?q=dance+classes&geo=60763&pid=3826&typeaheadRedirect=true&redirect=&startTime=1460253914937&uiOrigin=MASTHEAD&returnTo=__2F__&searchSessionId=405A7735978BFCBB83D06026999065331460239467712ssid#&ssrc=A&o=30')
html3 = PyQuery(url='https://www.tripadvisor.com/Search?q=dance+classes&geo=60763&pid=3826&typeaheadRedirect=true&redirect=&startTime=1460253914937&uiOrigin=MASTHEAD&returnTo=__2F__&searchSessionId=405A7735978BFCBB83D06026999065331460239467712ssid#&ssrc=A&o=60')

def parse_reviews(index, node):
    p = PyQuery(node)
    print p.text() + "\r\n"

def parse_url(index, node):
    element = PyQuery(node)
    onclickattr = element.attr['onclick']
    attrurl = onclickattr[onclickattr.index('\'/')+2:onclickattr.index('\')')]
    completeurl = baseUrl + attrurl
    print "processing: " + completeurl
    reviewPage = PyQuery(url=completeurl)
    reviewPage = reviewPage(".reviewSelector")
    i = 0
    reviewPage.each(parse_reviews)

def parse_review_urls(page):
    a = page(".result.ATTRACTIONS")
    a.each(parse_url)

parse_review_urls(html1)