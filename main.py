# Author:   Nicholai Mitchko
# File  :   main.py
# Desc  :   Python Script that scrapes reviews and codes them for research purposes (Json format)
# Date  :   4/6/2016

from pyquery import PyQuery
import json
import time
import requests
import re
from lxml import etree
import urllib

baseUrl = "https://www.tripadvisor.com/"

html1 = PyQuery(
    url='https://www.tripadvisor.com/Search?q=dance+classes&geo=60763&pid=3826&ssrc=A&o=0')

ReviewArray = []
i = 0
ReviewData = {}


def manual_parse(index, node):
    global ReviewArray, i
    i += 1
    review = PyQuery(node)
    ReviewArray.append({})
    ReviewArray[i]['ProviderName'] = ReviewData['ProviderName']
    ReviewArray[i]['ProviderLocation'] = ReviewData['Provider Location']
    ReviewArray[i]['ClassType'] = ReviewData['Class Type']
    ReviewArray[i]['ReviewType'] = ReviewData['Review Type']
    ReviewArray[i]['PointsRate'] = review('.sprite-rating_s_fill').attr['alt'][0:1]
    ReviewArray[i]['ReviewTitle'] = review('.noQuotes').text()
    ReviewArray[i]['ReviewerName'] = review('.username').text()
    location = review('.location').text()
    try:
        ReviewArray[i]['ReviewerLocationCity'] = location[0:location.index(',')]
        ReviewArray[i]['ReviewerLocationState'] = location[location.index(',') + 2:]
    except ValueError:
        ReviewArray[i]['ReviewerLocationState'] = location
        ReviewArray[i]['ReviewerLocationCity'] = ""
    ReviewArray[i]['ReviewNumPic'] = review('col2of2 > img').__len__()
    ReviewArray[i]['ReviewPicture'] = 'Yes' if ReviewArray[i]['ReviewNumPic'] > 0 else 'No'
    ReviewArray[i]['ReviewMobile'] = 'Yes' if review('.viaMobile').__len__() > 0 else 'No'
    try:
        review_date = time.strptime(review('.ratingDate').attr['title'].replace('Reviewed ', ''), "%B %d, %Y")
        ReviewArray[i]['ReviewDate'] = time.strftime("%m/%d/%y", review_date)
    except AttributeError:
        ReviewArray[i]['ReviewDate'] = "None found"
    ReviewArray[i]['ReviewHelpful'] = review('.numHlpIn').text()
    fullUrl = baseUrl + review('.col2of2').find('a').attr['href']
    reviewExpanded = PyQuery(url=fullUrl, parser='html')
    visitDate = time.strptime(reviewExpanded('.recommend-titleInline')[0].text.replace('Visited ', ''), '%B %Y')
    ReviewArray[i]['DateVisited'] = time.strftime('%m/%d', visitDate) if visitDate != 0 else "No Date Provided"
    ReviewArray[i]['ReviewText'] = reviewExpanded('.entry').find('[property="reviewBody"]').text()
    ReviewArray[i]['ReviewURL'] = fullUrl
    levelstring = review('.levelBadge').find('img').attr['src']
    ReviewArray[i]['ReviewerLevelContrib'] = levelstring[levelstring.index('lvl_') + 4:levelstring.index('.png')]
    ReviewArray[i]['ReviewerNumHelpful'] = re.sub(r"\D", "", review('.helpfulVotesBadge').find('span').text())
    member = PyQuery(url=baseUrl + 'members/' + ReviewArray[i]['ReviewerName'], parser='html')
    ReviewArray[i]['ReviewerPoints'] = re.sub(r"\D", "", member('.points_info').find('.points').text())
    ReviewArray[i]['ReviewerNumReviews'] = re.sub(r"\D", "",
                                                  member('li.content-info').find('a').filter('[name="reviews"]').text())
    ReviewArray[i]['ReviewerSince'] = member('.ageSince').find('p.since').text().replace('Since', '')
    ReviewArray[i]['ReviewerAge'] = member('.ageSince').find('p')[1].text
    ReviewArray[i]['ReviewerPhotos'] = re.sub(r"\D", "",
                                              member('li.content-info').find('a').filter('[name="photos"]').text())
    print i


def parse_review(review_page, url):
    global ReviewData
    ReviewData['ProviderName'] = review_page("#HEADING").text()
    ReviewData['Provider Location'] = review_page(".format_address").text().replace('Address: ', '')
    ReviewData['Class Type'] = 'Dance'
    solo_reviews = PyQuery(get_review(url, 5), parser='html')
    ReviewData['Review Type'] = 'Solo'
    solo_reviews('.reviewSelector').each(manual_parse)
    couple_reviews = PyQuery(get_review(url, 2), parser='html')
    ReviewData['Review Type'] = 'Couples'
    couple_reviews('.reviewSelector').each(manual_parse)


def parse_url_and_review(index, node):
    element = PyQuery(node)
    onclickattr = element.attr['onclick']
    attrurl = onclickattr[onclickattr.index('\'/') + 2:onclickattr.index('\')')]
    completeurl = baseUrl + attrurl
    print "processing: " + completeurl
    parse_review(PyQuery(url=completeurl, parser='html'), attrurl)


def parse_review_urls(page):
    a = page(".result.ATTRACTIONS")
    a.each(parse_url_and_review)


def get_review(url, type_):
    """
    :param url:
    :param type_: 5 for Solo 2 for Couples
    """
    r = requests.post(baseUrl + url, data={'mode': 'filterReviews',
                                           'filterRating': '',
                                           'filterSegment': type_,
                                           'filterSegment': '',
                                           'filterSeasons': '',
                                           'filterLang': 'en'})
    return r.content


ReviewLimits = {0, 30, 60}
SearchQuery = {}
parse_review_urls(html1)

print json.dumps(ReviewArray)
