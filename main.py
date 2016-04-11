# Author:   Nicholai Mitchko
# File  :   main.py
# Desc  :   Python Script that scrapes reviews and codes them for research purposes (Json format)
# Date  :   4/9/2016

from pyquery import PyQuery
import unicodecsv as csv
import json
import time
import requests
import copy
import re
from lxml import etree
import urllib2
from multiprocessing.dummy import Pool as ThreadPool

baseUrl = "https://www.tripadvisor.com/"


def manual_parse(node, ReviewData):
    review = PyQuery(node)
    reviewarray = {}
    reviewarray['ProviderName'] = ReviewData['ProviderName']
    reviewarray['ProviderLocation'] = ReviewData['Provider Location']
    reviewarray['ClassType'] = ReviewData['Class Type']
    reviewarray['ReviewType'] = ReviewData['Review Type']
    reviewarray['PointsRate'] = review('.sprite-rating_s_fill').attr['alt'][0:1]
    reviewarray['ReviewTitle'] = review('.noQuotes').text()
    reviewarray['ReviewerName'] = review('.username').text()
    location = review('.location').text()
    try:
        reviewarray['ReviewerLocationCity'] = location[0:location.index(',')]
        reviewarray['ReviewerLocationState'] = location[location.index(',') + 2:]
    except ValueError:
        reviewarray['ReviewerLocationState'] = location
        reviewarray['ReviewerLocationCity'] = ""
    reviewarray['ReviewNumPic'] = review('col2of2 > img').__len__()
    reviewarray['ReviewPicture'] = 'Yes' if reviewarray['ReviewNumPic'] > 0 else 'No'
    reviewarray['ReviewMobile'] = 'Yes' if review('.viaMobile').__len__() > 0 else 'No'
    try:
        review_date = time.strptime(review('.ratingDate').attr['title'].replace('Reviewed ', ''), "%B %d, %Y")
        reviewarray['ReviewDate'] = time.strftime("%m/%d/%y", review_date)
    except AttributeError:
        reviewarray['ReviewDate'] = "None found"
    reviewarray['ReviewHelpful'] = review('.numHlpIn').text()
    fullUrl = baseUrl + review('.col2of2').find('a').attr['href']
    reviewExpanded = PyQuery(url=fullUrl, parser='html')
    visitDate = time.strptime(reviewExpanded('.recommend-titleInline')[0].text.replace('Visited ', ''), '%B %Y')
    reviewarray['DateVisited'] = time.strftime('%m/%d', visitDate) if visitDate != 0 else "No Date Provided"
    reviewarray['ReviewText'] = reviewExpanded('.entry').find('[property="reviewBody"]').text()
    reviewarray['ReviewURL'] = fullUrl
    levelstring = review('.levelBadge').find('img').attr['src']
    try:
        reviewarray['ReviewerLevelContrib'] = levelstring[levelstring.index('lvl_') + 4:levelstring.index('.png')]
    except AttributeError:
        reviewarray['ReviewerLevelContrib'] = 'No Level Found'
    reviewarray['ReviewerNumHelpful'] = re.sub(r"\D", "", review('.helpfulVotesBadge').find('span').text())
    id = review('.col1of2').find('.memberOverlayLink').attr['id']
    userUrl = get_username(id[4:id.index('-')], id[id.index('SRC_') + 4:])
    member = PyQuery(url=baseUrl + userUrl, parser='html')
    reviewarray['ReviewerPoints'] = re.sub(r"\D", "", member('.points_info').find('.points').text())
    reviewarray['ReviewerNumReviews'] = re.sub(r"\D", "",
                                               member('li.content-info').find('a').filter('[name="reviews"]').text())
    reviewarray['ReviewerSince'] = member('.ageSince').find('p.since').text().replace('Since', '')
    try:
        reviewarray['ReviewerAge'] = member('.ageSince').find('p')[1].text
    except IndexError:
        reviewarray['ReviewerAge'] = 'No Age Found'
    reviewarray['ReviewerPhotos'] = re.sub(r"\D", "",
                                           member('li.content-info').find('a').filter('[name="photos"]').text())
    return reviewarray


def parse_review(review_page, url):
    print url
    reviewdata = {}
    reviewarray = []
    reviewdata['ProviderName'] = review_page("#HEADING").text()
    reviewdata['Provider Location'] = review_page(".format_address").text().replace('Address: ', '')
    reviewdata['Class Type'] = 'Dance'
    solo_reviews = PyQuery(get_review(url, 5), parser='html')
    reviewdata['Review Type'] = 'Solo'
    for x in solo_reviews('.reviewSelector').items():
        reviewarray.append(manual_parse(x, reviewdata).copy())
    couple_reviews = PyQuery(get_review(url, 2), parser='html')
    reviewdata['Review Type'] = 'Couples'
    for x in couple_reviews('.reviewSelector').items():
        reviewarray.append(manual_parse(x, reviewdata).copy())
    return reviewarray


def parse_url_and_review(attrurl):
    return parse_review(PyQuery(url=baseUrl + attrurl), attrurl)


def parse_review_urls(url_):
    page = PyQuery(url=url_, parser='html')
    urls = []
    for a in page(".result.ATTRACTIONS").items():
        onclickattr = PyQuery(a).attr['onclick']
        attrurl = onclickattr[onclickattr.index('\'/') + 2:onclickattr.index('\')')]
        urls.append(attrurl)
    print "Building Thread Pool"
    pool = ThreadPool(len(urls))
    print "Running " + str(len(urls)) + " Threads"
    results = pool.map(parse_url_and_review, urls)
    pool.close()
    pool.join()
    return results


def get_review(url, type_):
    """
    :param url:
    :param type_: 5 for Solo 2 for Couples
    """
    r = requests.post(baseUrl + url, data={'mode': 'filterReviews',
                                           'filterRating': '',
                                           'filterSegment': type_,
                                           'filterSeasons': '',
                                           'filterLang': 'en',
                                           'returnTo': ''})
    return r.content


def get_username(uid, src):
    r = requests.get('https://www.tripadvisor.com/MemberOverlay', params={'uid': uid,
                                                                          'c': '',
                                                                          'src': src,
                                                                          'fus': 'false',
                                                                          'partner': 'false',
                                                                          'Lsold': ''})
    R = PyQuery(r.content, parser='html')
    return R("a").attr['href']


var = raw_input("Enter Search Query: ")
print "Searching For", var
urlvar = urllib2.quote(var, ':/')
searchUrl = 'https://www.tripadvisor.com/Search?q=' + urlvar + '&geo=60763&pid=3826&ssrc=A&o='
print "Creafted Search URL: " + searchUrl
print "------------------------------"
x = 0
ReviewArray = []

while 1:
    print "Parsing " + str(x) + " - " + str(x + 30)
    r = parse_review_urls(searchUrl + str(x))
    if r[1] < 30:
        break
    x += 30

print "Writing JSON File:..."
with open('data_' + var + '.json', 'w') as outfile:
    json.dump(ReviewArray, outfile)

print "Writing CSV File:..."
with open('data_' + var + '.csv', 'wb') as f:  # Just use 'w' mode in 3.x
    w = csv.DictWriter(f, ReviewArray[0][0].keys(), encoding='utf-8')
    w.writeheader()
    for a in ReviewArray:
        w.writerows(a)
