#!/usr/bin/env python
# Author:   rewrite.py
# Desc  :   Python Script that scrapes reviews and codes them for research purposes (Json format)
# Date  :   4/12/2016

import TripAdvisor


def start():
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
    print "To scrape, enter any number of search queryies seperated by a comma"
    try:
        query = raw_input('TripAdvisor Query: ')
        print "Enter scrape parameters", "Leave blank and press enter for default values"
        types = {}
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
                    types = {"Group": 2}
                elif inp == 3:
                    types = {"Solo": 5, "Group": 2}
                elif inp == 4:
                    return
                else:
                    print "Bad Selection" + str(inp) + ", Try Again"
            elif inp == "":
                types = {"Solo": 5, "Group": 2}
            else:
                print "Incorrect Input, Try Again"
            break
        scraper = TripAdvisor.TripAdvisor(query=query, review_types=types, geo=60763)
        print "Scraping Reviews"
        scraper.parse_reviews()
        scraper.save_to_file(out_type={'csv'})
        print "Files Saved"
    except KeyboardInterrupt:
        pass


def handle_help():
    print "help"

print "Enter a command, or type help to get instructions"
start()
