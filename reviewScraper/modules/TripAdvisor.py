from pyquery import PyQuery
from itertools import repeat, izip
import requests
import re
import time
import json
import sys
import traceback
import unicodecsv as csv
import datetime
from lxml import etree
import urllib2
from multiprocessing.dummy import Pool


class TripAdvisor:
    searchURL = "https://www.tripadvisor.com/Search"
    baseURL = "https://www.tripadvisor.com/"
    genderMapping = {'male': 'M', 'female': 'F'}

    def __init__(self, query, review_types, result_type='A', geo=60763, page_limit=30, review_limit=15,
                 threading=30):
        self.searchQuery = query
        self.page_limit = page_limit
        self.reviewLimit = review_limit
        self.resultType = result_type
        self.reviewTypes = review_types
        self.geo = geo
        self.threading_multiple = threading
        self.searchAmount = 0
        self.reviewResults = []
        self.threading_done = False
        self.features = []
        self.labels = []
        # self.clf = tree.DecisionTreeClassifier()

    def save_to_file(self, out_type={'json', 'csv'}):
        filename = self.searchQuery + '_' + str(self.geo) + '_' + str(self.page_limit) + '_' + str(
            self.reviewLimit) + '_' + str(self.resultType)
        for i in out_type:
            if i == 'json':
                with open("data/scrape_" + filename + ".json", 'w') as outfile:
                    json.dump(self.reviewResults, outfile)
                print 'File Created', 'data/scrape_' + filename + '.json'
            if i == 'csv':
                with open('data/scrape_' + filename + '.csv', 'wb') as f:  # Just use 'w' mode in 3.x
                    w = csv.DictWriter(f, self.reviewResults[0][0].keys(), encoding='utf-8', extrasaction='ignore')
                    w.writeheader()
                    for a in self.reviewResults:
                        w.writerows(a)
                print 'File Created', 'data/scrape_' + filename + '.csv'

    def parse_reviews(self):
        self.searchAmount = 0
        for i in range(1, self.page_limit + 1):
            print "Page ", i, "/", self.page_limit, " In Progress"
            searchamt = 1
            urls = self.get_attraction_urls(self.search())
            amt = len(urls)
            searchamt += 1
            print "Reading reviews from next ", amt, " attractions"
            self.searchAmount += 30
            self.parse_pool(urls, process_num=self.threading_multiple)
            self.clean_list()
        print "Scraped", len(self.reviewResults), " reviews"
        self.threading_done = True

    def clean_list(self):
        while [] in self.reviewResults:
            self.reviewResults.remove([])

    def parse_pool(self, urls, process_num=3):
        # TODO: something with self.resultLimit
        # TODO: something with self.threading_multiple
        thread_pool = Pool(processes=min(process_num, len(urls)))
        self.reviewResults += thread_pool.map(TripAdvisor.threadCallHandler,
                                              izip(urls, repeat(self.reviewTypes), repeat(self.reviewLimit)))
        thread_pool.close()
        thread_pool.join()
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
        except Exception, e:
            return []

    @staticmethod
    def get_reviews_by_type(url, review_type_number, review_data, review_limit=5):
        filtered_reviews = PyQuery(TripAdvisor.get_review(url, review_type_number), parser='html')
        review_type = 'Hotel' if url.startswith('Hotel_Review') else 'Attraction'
        reviews = []
        for review in filtered_reviews('.reviewSelector').items():
            if review_limit < 1:
                break
            try:
                reviews.append(TripAdvisor.parse_single_review(review, review_data, review_type))
                review_limit -= 1
            except Exception:
                pass
        return reviews

    @staticmethod
    def get_counted_url(url, counter):
        if counter == 0:
            return url
        else:
            return url[url.index('Reviews') + 7:] + '-or' + str(counter) + url[:url.index('Reviews') + 7]

    @staticmethod
    def parse_single_review(node, review_data, review_type='Hotel'):
        if review_type == 'Hotel':
            hotel_review = HotelReview(node, review_data)
            hotel_review.process_all()
            return hotel_review.scraped_review
        else:
            attraction_review = AttractionReview(node, review_data)
            attraction_review.process_all()
            return attraction_review.scraped_review

    @staticmethod
    def get_start_date_string(text):
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
        req = requests.get(TripAdvisor.baseURL + url, allow_redirects=True)
        return requests.post(req.url, data={'mode': 'filterReviews',
                                            'filterRating': '',
                                            'filterSegment': type_,
                                            'filterSeasons': '',
                                            'filterLang': 'en',
                                            'returnTo': ''}).content

    @staticmethod
    def get_review_info(review_page):
        return {'ProviderName': review_page("#HEADING").text(),
                'Provider Location': review_page(".format_address").text().replace('Address: ', ''),
                'Class Type': ''}

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
            attribute = PyQuery(item).children().attr['onclick']
            urls.append(attribute[attribute.index('\'/') + 2: attribute.index('\')')])
        if len(urls) == 0:
            for item in page(".listing_title").items():
                attribute = PyQuery(item).children().attr['href']
                urls.append(attribute[1:])
        return urls

    @staticmethod
    def get_filtered_reviews(attraction_url, review_type):
        return requests.post(TripAdvisor.baseURL + attraction_url, data={'mode': 'filterReviews',
                                                                         'filterRating': '',
                                                                         'filterSegment': review_type,
                                                                         'filterSeasons': '',
                                                                         'filterLang': 'en',
                                                                         'returnTo': ''}).content

    @staticmethod
    def search_bar(query):
        return json.loads(requests.get(TripAdvisor.baseURL + 'TypeAheadJson', params={
            'interleaved': 'true',
            'geoPages': 'true',
            'details': 'false',
            'types': 'geo,hotel,eat,attr,vr,air,theme_park,al,act',
            'link_type': 'geo',
            'matchTags': 'false',
            'matchGlobalTags': 'true',
            'matchKeywords': 'true',
            'strictAnd': 'false',
            'scoreThreshold': 0.8,
            'hglt': 'true',
            'disableMaxGroupSize': 'true',
            'max': 10,
            'allowPageInsertionOnGeoMatch': 'false',
            'startTime': int(datetime.datetime.now().strftime("%s")) * 1000,  # startTime is the milliseconds from epoch
            'action': 'API',
            'source': 'MASTHEAD',
            'uiOrigin': 'MASTHEAD',
            'query': query
        }).content)


class Review:
    def __init__(self, node, review_data):
        self.review = PyQuery(node)
        self.scraped_review = {'ProviderName': review_data['ProviderName'],
                               'ProviderLocation': review_data['Provider Location'],
                               'ClassType': review_data['Class Type'], 'ReviewType': review_data['Review Type']}
        self.full_review = None
        self.member = None

    def review_title(self):
        self.scraped_review['Title'] = self.review('.noQuotes').text()

    def reviewer_username(self):
        self.scraped_review['Username'] = self.review('.username').text()

    def review_location(self):
        location = self.review('.location').text()
        try:
            self.scraped_review['ReviewerLocationCity'] = location[0:location.index(',')]
            self.scraped_review['ReviewerLocationState'] = location[location.index(',') + 2:]
        except ValueError:
            self.scraped_review['ReviewerLocationState'] = "NA"
            self.scraped_review['ReviewerLocationCity'] = location

    def review_has_picture(self):
        self.scraped_review['ReviewPicture'] = '1' if self.scraped_review['ReviewNumPic'] > 0 else '0'

    def review_mobile(self):
        self.scraped_review['ReviewMobile'] = '1' if self.review('.viaMobile').__len__() > 0 else '0'

    def review_date(self):
        try:
            review_date = time.strptime(self.review('.ratingDate').text().replace('Reviewed ', ''), "%B %d, %Y")
            self.scraped_review['ReviewDate'] = time.strftime("%m/%d/%y", review_date)
        except ValueError:
            review_date = time.strptime(self.review('.ratingDate').attr['title'].replace('Reviewed ', ''), "%B %d, %Y")
            self.scraped_review['ReviewDate'] = time.strftime("%m/%d/%y", review_date)
        except Exception:
            self.scraped_review['ReviewDate'] = datetime.datetime.now().strftime("%m/%d/%y")

    def review_helpful(self):
        self.scraped_review['ReviewHelpful'] = self.review('.numHlpIn').text()

    def review_number_of_pictures(self):
        self.scraped_review['ReviewNumPic'] = self.review('col2of2').find('img').__len__()

    def load_full_review(self):
        full_url = TripAdvisor.baseURL + self.review('.col2of2').find('a').attr['href']
        self.scraped_review['ReviewURL'] = full_url
        self.full_review = PyQuery(url=full_url, parser='html')

    def review_text(self):
        self.scraped_review['ReviewText'] = self.full_review('.entry').find('[property="reviewBody"]').text()

    def review_date_visited(self):
        visit_date = time.strptime(re.sub(r", traveled.*", "", re.sub(r"(Visited|Stayed).", "",
                                                                      self.full_review('.recommend-titleInline')[
                                                                          0].text)), '%B %Y')
        self.scraped_review['DateVisited'] = time.strftime('%m/%d/%Y', visit_date) if visit_date != 0 else "NA"

    def reviewer_level_contributor(self):
        self.scraped_review['ReviewerLevelContrib'] = ''
        try:
            level_string = self.review('.levelBadge').find('img').attr['src']
            self.scraped_review['ReviewerLevelContrib'] = level_string[
                                                          level_string.index('lvl_') + 4:level_string.index('.png')]
        except ValueError:
            pass
        except AttributeError:
            pass

    def review_number_helpful(self):
        self.scraped_review['ReviewerNumHelpful'] = re.sub(r"\D", "",
                                                           self.review('.helpfulVotesBadge').find('span').text())

    def review_thanked(self):
        thanked = self.review('.numHlpIn').text()
        self.scraped_review['ReviewThanked'] = 0 if thanked == '' else thanked

    def get_user_page(self):
        id_ = self.review('.col1of2').find('.memberOverlayLink').attr['id']
        self.member = PyQuery(
            url=TripAdvisor.baseURL + TripAdvisor.get_username(id_[4:id_.index('-')], id_[id_.index('SRC_') + 4:]),
            parser='html')

    def get_user_points(self):
        self.scraped_review['ReviewerPoints'] = re.sub(r"\D", "", self.member('.points_info').find('.points').text())

    def get_user_number_reviews(self):
        self.scraped_review['ReviewerNumReviews'] = re.sub(r"\D", "",
                                                           self.member('li.content-info').find('a').filter(
                                                               '[name="reviews"]').text())

    def get_user_inception(self):
        self.scraped_review['ReviewerSince'] = TripAdvisor.get_start_date_string(
            self.member('.ageSince').find('p.since').text().replace('Since ', ''))

    def get_user_age(self):
        try:
            # There is more to do here than just get the text,
            # TODO: implement and age column and more...
            self.scraped_review['ReviewerAge'] = self.member('.ageSince').find('p')[1].text
        except IndexError:
            self.scraped_review['ReviewerAge'] = ''

    def get_user_gender(self):
        member_html = self.member('.ageSince').html().lower()
        for sex, sex_letter in TripAdvisor.genderMapping.iteritems():
            try:
                if member_html.index(sex) != -1:
                    self.scraped_review['ReviewerGender'] = sex_letter
            except ValueError:
                pass

    def get_reviewer_photos(self):
        self.scraped_review['ReviewerPhotos'] = re.sub(r"\D", "",
                                                       self.member('li.content-info').find('a').filter(
                                                           '[name="photos"]').text())

    def process(self):
        self.load_full_review()
        self.get_user_page()
        self.review_title()
        self.reviewer_username()
        self.review_location()
        self.review_number_of_pictures()
        self.review_has_picture()
        self.review_mobile()
        self.review_date()
        self.review_date_visited()
        self.review_helpful()
        self.review_text()
        self.reviewer_level_contributor()
        self.review_number_helpful()
        self.review_thanked()
        self.get_user_points()
        self.get_user_number_reviews()
        self.get_user_inception()
        self.get_user_age()
        self.get_user_gender()
        self.get_reviewer_photos()


class AttractionReview(Review):
    def get_review_rating(self):
        self.scraped_review['Rating'] = self.review('.sprite-rating_s_fill').attr['alt'][0:1]

    def process_all(self):
        self.process()
        self.get_review_rating()


class HotelReview(Review):
    def get_review_rating(self):
        self.scraped_review['Rating'] = int(
            self.review('.ui_bubble_rating').attr['class'].replace('ui_bubble_rating bubble_', '')) / 10

    def process_all(self):
        self.process()
        self.get_review_rating()
