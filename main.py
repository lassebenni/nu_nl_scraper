from scrape.scraper import scrape_headlines
from models.headline import store_headlines

PATH = "output/results.json"


if __name__ == "__main__":
    headlines = scrape_headlines()
    store_headlines(PATH, headlines)
