import logging
from typing import List
from models.headline import Headline, store_headlines
from bs4 import BeautifulSoup as bs
import requests

logger = logging.getLogger(__name__)

URL = "https://www.nu.nl/meest-gelezen"


def scrape_headlines() -> List[Headline]:
    headlines: List[Headline] = []

    feed = requests.get(URL)

    if not feed or not feed.text:
        logger.error("Could not fetch feed")
        return []

    soup = bs(feed.text)
    headline_list_elements = soup.find_all("ul", class_="list list--datetime")

    if not headline_list_elements:
        logger.error("No headlines found.")
        return []

    ranking = 1  # "most read" ranking for each article

    for list_element in headline_list_elements:
        article_elements = list_element.find_all("a", class_="list__link")

        for article_element in article_elements:
            title = article_element.find("span").text
            url = article_element["href"]

            headline = Headline(
                title=title.strip(),
                summary="",
                url=f"https://www.nu.nl{url}",
                rank=ranking,
            )
            ranking += 1
            headlines.append(headline)

    return headlines
