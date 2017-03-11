#!/usr/bin/env python
# Author:   rewrite.py
# Desc  :   Python Script that scrapes reviews and codes them for research purposes (Json format)
# Date  :   4/12/2016
import TripAdvisor


def start():
    print "scrape\r\n\t\tPull reviews from TripAdvisor with a single query"
    print "queue\r\n\t\tPull reviews from TripAdvisor with a queue of queries"
    print "exit\r\n\t\tQuit application"
    try:
        while True:
            input = raw_input('> ')
            tokens = input.split()
            command = tokens[0]
            args = tokens[1:]
            if command == 'scrape':
                handle_scrape()
            elif command == 'exit':
                break
            elif command == 'queue':
                handle_queue()
            elif command == 'settings':
                print "settings"
            elif command == 'assignment':
                handle_assignment()
            else:
                handle_help()
    except KeyboardInterrupt:
        pass


def handle_scrape():
    print "To scrape, enter a search query"
    try:
        query = raw_input('TripAdvisor Query: ')
        types = {}
        page_limit = 1
        reviewLimit = 5
        while True:
            print ""
            print "1    Solo Reviews Only"
            print "2    Group Reviews Only"
            print "3    Both Review Types"
            print "4    Return"
            print ""
            inp = input("Type Number>")
            if isinstance(inp, int):
                if inp == 1:
                    types = {"Solo": 5}
                elif inp == 2:
                    types = {"Couples": 2}
                elif inp == 3:
                    types = {"Solo": 5, "Couples": 2}
                elif inp == 4:
                    return
                else:
                    print "Bad Selection" + str(inp) + ", Try Again"
            else:
                print "Default Values used types = {\"Solo\": 5, \"Couples\": 2}"
                types = {"Solo": 5, "Couples": 2}
            break
        geocode = 60763
        input_geocode = input("Enter geo code>")
        if isinstance(input_geocode, int):
            geocode = input_geocode
        scraper = TripAdvisor.TripAdvisor(query=query, review_types=types, geo=geocode, page_limit=page_limit,
                                         review_limit=reviewLimit, result_type='a', threading=5)
        # print "Scraping Reviews"
        scraper.parse_reviews()
        scraper.save_to_file(out_type={'csv'})
    except KeyboardInterrupt:
        pass


def handle_assignment():
    page_limit = 1
    reviewLimit = 5
    types = {"Solo": 5, "Couples": 2}
    for query in ['restaurants', 'hotels', 'museums']:
            for geocode in [56003,60763,60795,32655,35805]:
                print "Scraping Reviews ", query, " ", geocode
                scraper = TripAdvisor.TripAdvisor(query=query, review_types=types, geo=geocode, page_limit=page_limit,
                                          review_limit=reviewLimit, result_type='a', threading=5)
                scraper.parse_reviews()
                scraper.save_to_file(out_type={'json'})


def handle_queue():
    print "To scrape in a queue enter a list of queries and geocodes"
    try:
        qu = raw_input('TripAdvisor Query List (seperate by comma):')
        query_list = qu.split(',')
        types = {}
        page_limit = 1
        reviewLimit = 5
        while True:
            print ""
            print "1    Solo Reviews Only"
            print "2    Group Reviews Only"
            print "3    Both Review Types"
            print "4    Return"
            print ""
            inp = input("Type Number>")
            if isinstance(inp, int):
                if inp == 1:
                    types = {"Solo": 5}
                elif inp == 2:
                    types = {"Couples": 2}
                elif inp == 3:
                    types = {"Solo": 5, "Couples": 2}
                elif inp == 4:
                    return
                else:
                    print "Bad Selection" + str(inp) + ", Try Again"
            else:
                print "Default Values used types = {\"Solo\": 5, \"Couples\": 2}"
                types = {"Solo": 5, "Couples": 2}
            break
        # geocode = 60763
        input_geocode = raw_input("Geocode List (seperate by comma):")
        geocode_list = input_geocode.split(',')
        print input_geocode
        print qu
        # if isinstance(input_geocode, int):
        #    geocode = input_geocode
        for query in query_list:
            for geocode in geocode_list:
                print 'Geocode:\t', geocode
                print 'Query  :\t', query
                geo_ = int(geocode)
                scraper = TripAdvisor.TripAdvisor(query=query, review_types=types, geo=geo_, page_limit=page_limit,
                                          review_limit=reviewLimit, result_type='a', threading=5)
                scraper.parse_reviews()
                scraper.save_to_file(out_type={'csv'})
    except KeyboardInterrupt:
        pass


def handle_help():
    print "help"
