#!/usr/bin/env python
# Author:   rewrite.py
# Desc  :   Python Script that scrapes reviews and codes them for research purposes (Json format)
# Date  :   4/12/2016

import TripAdvisor


def start():
    print "Type 'scrape' to get started"
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
            elif command == 'settings':
                print "settings"
            else:
                handle_help()
    except KeyboardInterrupt:
        pass


def handle_scrape():
    print "To scrape, enter a search query"
    try:
        query = raw_input('TripAdvisor Query: ')
        types = {}
        limit = 30
        reviewLimit = 15
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
        while True:
            print ""
            print "Enter The Maximum Number of Attractions to Parse"
            inp = input("Type Number>")
            if isinstance(inp, int):
                limit = inp
            else:
                print "Default Value used", str(30)
            break
        while True:
            print ""
            print "Enter The Maximum Number of Reviews Per Attraction to Parse"
            inp = input("Type Number>")
            if isinstance(inp, int):
                reviewLimit = inp
            else:
                print "Default Value used", str(30)
            break
        scraper = TripAdvisor.TripAdvisor(query=query, review_types=types, geo=60763, result_limit=limit, review_limit=reviewLimit)
        print "Scraping Reviews"
        scraper.parse_reviews()
        scraper.save_to_file(out_type={'csv'})
    except KeyboardInterrupt:
        pass


def handle_help():
    print "help"

start()
