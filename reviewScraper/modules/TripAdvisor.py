from pyquery import PyQuery
from itertools import repeat, izip
import requests
import re
import time
import json
import sys
from sklearn import tree
# import traceback
import unicodecsv as csv
import datetime
from lxml import etree
import urllib2
from multiprocessing.dummy import Pool


class TripAdvisor:
    searchURL = "https://www.tripadvisor.com/Search"
    baseURL = "https://www.tripadvisor.com/"
    genderMapping = {'male': 'M', 'female': 'F'}

    def __init__(self, query, review_types, result_type='A', geo=60763, result_limit=30, review_limit=15,
                 threading=30):
        self.searchQuery = query
        self.resultLimit = result_limit
        self.reviewLimit = review_limit
        self.resultType = result_type
        self.reviewTypes = review_types
        self.geo = geo
        self.threading_multiple = min(threading, 30)
        self.searchAmount = 0
        self.reviewResults = []
        self.threading_done = False
        self.features = []
        self.labels = []
        self.clf = tree.DecisionTreeClassifier()

    def save_to_file(self, out_type={'json', 'csv'}):
        filename = self.searchQuery + '_' + str(self.geo) + '_' + str(self.resultLimit) + '_' + str(
            self.reviewLimit) + '_' + str(self.resultType)
        for i in out_type:
            if i == 'json':
                with open("data/scrape_" + filename + ".json", 'w') as outfile:
                    json.dump(self.reviewResults, outfile)
                print 'File Created', 'data/scrape_' + filename + '.json'
            if i == 'csv':
                with open('data/scrape_' + filename + '.csv', 'wb') as f:  # Just use 'w' mode in 3.x
                    w = csv.DictWriter(f, self.reviewResults[0][0].keys(), encoding='utf-8')
                    w.writeheader()
                    for a in self.reviewResults:
                        w.writerows(a)
                print 'File Created', 'data/scrape_' + filename + '.csv'

    def parse_reviews(self):
        self.searchAmount = 0
        sa = 0
        while 1:
            urls = self.get_attraction_urls(self.search())
            remaining = min(self.resultLimit - len(self.reviewResults), 30)
            print ""
            print "Trying ", remaining, " Remaining Attractions"
            if len(urls) == 0 or remaining <= 0:
                break
            if remaining < 30:
                urls = urls[:remaining]
            self.searchAmount += 30
            print "Scraping ", remaining, " URLS"
            self.parse_pool(urls, process_num=self.threading_multiple)
            self.clean_list()
        print "I found", len(self.reviewResults), " Attractions"
        self.threading_done = True

    def clean_list(self):
        while [] in self.reviewResults:
            self.reviewResults.remove([])

    def parse_pool(self, urls, process_num=30):
        # TODO: something with self.resultLimit
        # TODO: something with self.threading_multiple
        threadPool = Pool(processes=min(process_num, len(urls)))
        self.reviewResults += threadPool.map(TripAdvisor.threadCallHandler,
                                             izip(urls, repeat(self.reviewTypes), repeat(self.reviewLimit)))
        threadPool.close()
        threadPool.join()
        sys.stdout.flush()

    @staticmethod
    def threadCallHandler(a_b_c):
        return TripAdvisor.makereview(*a_b_c)

    @staticmethod
    def makereview(url, review_types, review_limit):
        try:
            review_page = PyQuery(TripAdvisor.baseURL + url, parser='html')
            review_data = TripAdvisor.get_review_info(review_page)
            pageReviews = []
            for Name, Type in review_types.iteritems():
                review_data['Review Type'] = Name
                pageReviews += TripAdvisor.get_reviews_by_type(url, Type, review_data, review_limit)
            return pageReviews
        except Exception:
            return []

    @staticmethod
    def get_reviews_by_type(attraction_url, review_type_number, review_data, review_limit=5):
        # rl = review_limit
        # reviews = []
        # counter = 0
        # # while 1:
        # #     counter_url = TripAdvisor.getCountedURL(attraction_url, counter)
        # #     counter += 10
        # #     print counter_url.index('-or')
        # #     filtered_reviews = PyQuery(TripAdvisor.get_review(counter_url, review_type_number), parser='html')
        # #     i = False
        # #     for review in filtered_reviews('.reviewSelector').items():
        # #         i = True
        # #         if rl < 1:
        # #             return reviews
        # #         reviews.append(TripAdvisor.parse_single_review(review, review_data))
        # #         rl -= 1
        # #     if not i:
        # #         return reviews
        counter = 0
        filtered_reviews = PyQuery(TripAdvisor.get_review(attraction_url, review_type_number), parser='html')
        reviews = []
        for review in filtered_reviews('.reviewSelector').items():
            if review_limit < 1:
                return reviews
            reviews.append(TripAdvisor.parse_single_review(review, review_data))
            review_limit -= 1
        return reviews

    @staticmethod
    def getCountedURL(url, counter):
        if counter == 0:
            return url
        else:
            return url[url.index('Reviews') + 7:] + '-or' + str(counter) + url[:url.index('Reviews') + 7]

    @staticmethod
    def parse_single_review(node, review_data):
        review = PyQuery(node)
        reviewarray = {}
        reviewarray['ProviderName'] = review_data['ProviderName']
        reviewarray['ProviderLocation'] = review_data['Provider Location']
        reviewarray['ClassType'] = review_data['Class Type']
        reviewarray['ReviewType'] = review_data['Review Type']
        reviewarray['PointsRate'] = review('.sprite-rating_s_fill').attr['alt'][0:1]
        reviewarray['ReviewTitle'] = review('.noQuotes').text()
        reviewarray['ReviewerName'] = review('.username').text()
        location = review('.location').text()
        try:
            reviewarray['ReviewerLocationCity'] = location[0:location.index(',')]
            reviewarray['ReviewerLocationState'] = location[location.index(',') + 2:]
        except ValueError:
            reviewarray['ReviewerLocationState'] = "NA"
            reviewarray['ReviewerLocationCity'] = location
        reviewarray['ReviewNumPic'] = review('col2of2').find('img').__len__()
        reviewarray['ReviewPicture'] = 'Yes' if reviewarray['ReviewNumPic'] > 0 else 'No'
        reviewarray['ReviewMobile'] = 'Yes' if review('.viaMobile').__len__() > 0 else 'No'
        try:
            review_date = time.strptime(review('.ratingDate').text().replace('Reviewed ', ''), "%B %d, %Y")
            reviewarray['ReviewDate'] = time.strftime("%m/%d/%y", review_date)
        except ValueError:
            review_date = time.strptime(review('.ratingDate').attr['title'].replace('Reviewed ', ''), "%B %d, %Y")
            reviewarray['ReviewDate'] = time.strftime("%m/%d/%y", review_date)
        except Exception:
            reviewarray['ReviewDate'] = datetime.datetime.now().strftime("%m/%d/%y")
        reviewarray['ReviewHelpful'] = review('.numHlpIn').text()
        fullUrl = TripAdvisor.baseURL + review('.col2of2').find('a').attr['href']
        reviewExpanded = PyQuery(url=fullUrl, parser='html')
        visitDate = time.strptime(reviewExpanded('.recommend-titleInline')[0].text.replace('Visited ', ''), '%B %Y')
        reviewarray['DateVisited'] = time.strftime('%m/%d', visitDate) if visitDate != 0 else "NA"
        reviewarray['ReviewText'] = reviewExpanded('.entry').find('[property="reviewBody"]').text()
        reviewarray['ReviewURL'] = fullUrl
        levelstring = review('.levelBadge').find('img').attr['src']
        try:
            reviewarray['ReviewerLevelContrib'] = levelstring[levelstring.index('lvl_') + 4:levelstring.index('.png')]
        except AttributeError:
            reviewarray['ReviewerLevelContrib'] = 0
        reviewarray['ReviewerNumHelpful'] = re.sub(r"\D", "", review('.helpfulVotesBadge').find('span').text())
        id_ = review('.col1of2').find('.memberOverlayLink').attr['id']
        userUrl = ""
        reviewarray['ReviewerSince'] = 'NA'
        reviewarray['ReviewerPoints'] = 0
        reviewarray['ReviewerSince'] = 0
        reviewarray['ReviewerGender'] = 'NA'
        reviewarray['ReviewerAge'] = 'NA'
        reviewarray['ReviewerPhotos'] = 0
        try:
            userUrl = TripAdvisor.get_username(id_[4:id_.index('-')], id_[id_.index('SRC_') + 4:])
        except Exception, e:
            pass
        member = PyQuery(url=TripAdvisor.baseURL + userUrl, parser='html')
        reviewarray['ReviewerPoints'] = re.sub(r"\D", "", member('.points_info').find('.points').text())
        reviewarray['ReviewerNumReviews'] = re.sub(r"\D", "",
                                                   member('li.content-info').find('a').filter(
                                                       '[name="reviews"]').text())

        reviewarray['ReviewerSince'] = TripAdvisor.getStartDateString(
            member('.ageSince').find('p.since').text().replace('Since ', ''))
        memberHTML = member('.ageSince').html().lower()
        reviewarray['ReviewerGender'] = 'NA'
        for sex, sexlttr in TripAdvisor.genderMapping.iteritems():
            try:
                if memberHTML.index(sex) != -1:
                    reviewarray['ReviewerGender'] = sexlttr
            except ValueError:
                pass
        try:
            reviewarray['ReviewerAge'] = member('.ageSince').find('p')[1].text
        except IndexError:
            reviewarray['ReviewerAge'] = 'NA'
        reviewarray['ReviewerPhotos'] = re.sub(r"\D", "",
                                               member('li.content-info').find('a').filter('[name="photos"]').text())
        return reviewarray

    @staticmethod
    def getStartDateString(text):
        try:
            if text.index('this') != -1:
                return datetime.datetime.now().strftime('%m/%y')
        except ValueError:
            pass
        try:
            if text.index('today') != -1:
                return datetime.datetime.now().strftime('%m/%y')
        except ValueError:
            pass
        return time.strftime("%m/%y", time.strptime(text, '%b %Y'))

    @staticmethod
    def get_review(url, type_):
        """
        :param url:
        :param type_: 5 for Solo 2 for Couples
        """
        r = requests.post(TripAdvisor.baseURL + url, data={'mode': 'filterReviews',
                                                           'filterRating': '',
                                                           'filterSegment': type_,
                                                           'filterSeasons': '',
                                                           'filterLang': 'en',
                                                           'returnTo': ''})
        return r.content

    @staticmethod
    def get_review_info(review_page):
        review_info = {}
        review_info['ProviderName'] = review_page("#HEADING").text()
        review_info['Provider Location'] = review_page(".format_address").text().replace('Address: ', '')
        review_info['Class Type'] = 'Dance'
        return review_info

    def search(self):
        return requests.get(TripAdvisor.searchURL, params={'q': self.searchQuery,
                                                           'geo': self.geo,
                                                           'ssrc': self.resultType,
                                                           'pid': '3826',
                                                           'o': self.searchAmount}).content

    @staticmethod
    def get_username(uid, src):
        r = requests.get('https://www.tripadvisor.com/MemberOverlay', params={'uid': uid,
                                                                              'c': '',
                                                                              'src': src,
                                                                              'fus': 'false',
                                                                              'partner': 'false',
                                                                              'Lsold': ''})
        R = PyQuery(r.content, parser='html')
        return R("a").attr['href']

    @staticmethod
    def get_attraction_urls(search_results):
        urls = []
        page = PyQuery(search_results, parser='html')
        for item in page(".result").items():
            attribute = PyQuery(item).attr['onclick']
            urls.append(attribute[attribute.index('\'/') + 2: attribute.index('\')')])
        return urls

    @staticmethod
    def get_filtered_reviews(attraction_url, review_type):
        return requests.post(TripAdvisor.baseURL + attraction_url, data={'mode': 'filterReviews',
                                                                         'filterRating': '',
                                                                         'filterSegment': review_type,
                                                                         'filterSeasons': '',
                                                                         'filterLang': 'en',
                                                                         'returnTo': ''}).content

    def initneural(self):
        with open('trainingData/TrainingData1.csv', 'rb') as csvfile:
            csvreader = csv.reader(csvfile, dialect='excel')
            for row in csvreader:
                self.features.append([row['A'], row['B']])
                self.labels.append(1)
        with open('trainingData/TrainingData0.csv', 'rb') as csvfile:
            csvreader = csv.reader(csvfile, dialect='excel')
            for row in csvreader:
                self.features.append([row['A'], row['B']])
                self.labels.append(0)
        self.clf = self.clf.fit(self.features, self.labels)


