from scrape.rss_parser import parse_headlines
from scrape.scraper import scrape_headlines
from models.headline import store_headlines

PATH = "output/results.json"


def main():
    # headlines = parse_headlines(PATH)
    headlines = scrape_headlines(PATH)
    store_headlines(headlines)


if __name__ == "__main__":
    main()
