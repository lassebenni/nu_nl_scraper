import logging
from typing import List
from models.headline import Headline, store_headlines
from bs4 import BeautifulSoup as bs
import requests

logger = logging.getLogger(__name__)

URL = "https://www.nu.nl/meest-gelezen"


def scrape_headlines() -> List[Headline]:
    res: List[Headline] = []

    feed = requests.get(URL)

    if not feed or not feed.text:
        logger.error("Could not fetch feed")
        return []

    soup = bs(feed.text)
    # headlines = soup.find_all("ul", class_="list list--datetime")

    nu_headlines = soup.select("ul.contentlist > li > a")

    if not nu_headlines:
        logger.error("No headlines found.")
        return []

    ranking = 1  # "most read" ranking for each article

    for headline in nu_headlines:
        title = headline.find("span").text
        url = headline["href"]

        headline = Headline(
            title=title.strip(),
            summary="",
            url=f"https://www.nu.nl{url}",
            rank=ranking,
        )
        ranking += 1
        res.append(headline)

    return res
