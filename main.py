from scrape.rss_parser import (
    parse_headlines,
    read_previous_headlines,
    store_headlines,
    drop_duplicates,
)

PATH = "output/results.json"


def main():
    headlines = parse_headlines()

    prev_headlines = read_previous_headlines(PATH)

    headlines = drop_duplicates(headlines + prev_headlines)

    store_headlines(PATH, headlines)


if __name__ == "__main__":
    main()
