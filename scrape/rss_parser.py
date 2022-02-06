from typing import List
from models.headline import Headline
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
