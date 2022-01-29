import json
from typing import List
from models.headline import Headline, create_unique_id

import feedparser

URL = "https://www.nu.nl/rss/Algemeen"


def parse_headlines() -> List[Headline]:
    headlines: List[Headline] = []

    feed = feedparser.parse(URL)
    if feed:
        for entry in feed.entries:
            headline = Headline(**entry)
            headlines.append(headline)

    return headlines


def drop_duplicates(headlines: List[Headline]):
    unique_headlines: List[Headline] = []
    unique_ids = []

    for headline in headlines:
        if not headline.id and headline.title:
            headline["id"] = create_unique_id(headline.title)

        if headline.id not in unique_ids:
            unique_ids.append(headline.id)
            unique_headlines.append(headline)
        else:
            continue

    return unique_headlines


def read_previous_headlines(path: str) -> List[Headline]:
    headlines: List[Headline] = []

    with open(path, "r") as f:
        text = f.read()

        if text:
            json_headlines = json.loads(text)
            for headline_json in json_headlines:
                headlines.append(Headline(**headline_json))

    return headlines


def store_headlines(path: str, headlines: List[Headline], as_json: bool = True):
    with open(path, "w") as f:
        if as_json:
            headlines = [headline.dict() for headline in headlines]

        f.write(json.dumps(headlines, default=str))
