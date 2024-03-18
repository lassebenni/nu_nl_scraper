import logging
from typing import List
from models.headline import Headline, store_headlines
from bs4 import BeautifulSoup as bs
import requests

logger = logging.getLogger(__name__)

URL = "https://www.nu.nl/meest-gelezen"

payload = {}
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Cookie": "consentUUID=16ec7356-f2e4-4efd-b2ad-1e3ff7271848_27; CookieConsent=CP3ptYAP3ptYAAGABCENAeEoAPLAAAAAABpYIzNBxDIUBQFCMXJ6SJswWIQX5kAAIgAQAAYBAyABhBoAIAQCkEESFATAAAACAAAAIAIAIABAGAAAAAAQQAABAAGASAAAgAIIICAAgAIBQAAIAAAAAAAAAAAAgAAAAAAAkAAAAAIgWEgAFAAAAAAAIAgAAAABAgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAAAAUEgMgALAAqAB4AEAAMgAaABEACYAE8AMwAbwA_ACEgEQARIAwABlQDuAO8AfoBIgCUgI9AXmAyQBk4DPggAIAjgBOw0AEBnwiACAz4dAfAAWABUAEAAMgAaABEACYAE8AMQAZgA3gB-gEQARIAwABlADRgHcAd4A_QCLAEiAJSAc4A6gCLwEegJkAXmAyQBk4DLAGfDgBAA6ACEAERAI4ATsBMQDBAGTEoBwACwAiABMADFAIgAiQBgADvAOoAi8BHoC8wGSAMnAZ8SACADuAI4AmIBlhSA4AAsACoAIAAZAA0ACIAEwAJ4AYgAzAB-gEQARIAwABlADRAHeAP0AiwBIgCUgHUAReAj0BeYDJAGTgMsAZ8UADAAKAHcAXUBMQDBAGTAAAA.YAAAAAAAAAAA; euconsent-v2=CPz10AAPz10AAAGABBENATEgAAAAAAAAACiQAAAAAAAA.YAAAAAAAAAAA; authUt=1; consentDate=2023-10-18T16:06:57.433Z; temptation-id=ts-d0eaeb7b-0515-4fb5-93e5-10eeaeb687a2; last_visit_timestamp=1710791636; _sp_su=false; __sectionViewCount-buitenland=26; authId=39aed31d-b386-42f5-b58c-06bf63ff61f8; __sectionViewCount-binnenland=9; __sectionViewCount-misdaad=1; __sectionViewCount-tech=2; __sectionViewCount-weerbericht=1; __sectionViewCount-verkiezingen-vs=1; __sectionViewCount-economie=1; __sectionViewCount-achterklap=2; __sectionViewCount-uitleg-over-het-coronavirus=1; __sectionViewCount-voetbal=1; gig_canary=false; gig_canary_ver=12940-3-27471510; s_id=d54964d2-0a8c-4abd-91f1-ced9b7ea71f0; gtmSessionStatus=true; usbls=1; x-oidcp-logintype=POST_PASSWORD_RESET_WITH_CHALLENGE; x-oidcp-audience=b098fa91cf6846626bee519cc94ff232f695fa644face06a696f36e614ec6e10; x-push-device-token=A7DrKxXEn2EB8P1E2WeLUZLWQg5Fe9Hi5vYgYbgUZ5BRKdJSZmeP4shyP55qfNU; ak_bmsc=AD0F3DEFAEB2B5C41119305845F31870~000000000000000000000000000000~YAAQqf1IF5jVdU2OAQAAdBMgUxc3iT3i2j61I7RnmmluiW+Ewo7a3M0+3JZzT8nrD7ra0WqNExX5v8UjxzvdJ+mkqIDhblTAs4ui6ucc5Zo9ispiNe3nObvCgKWdRNRvyOEuxQNLqnEr1S1l/raHLn0nr6AkiGEGq+fDULl8s/+iEDSk6utKvTilG0e3Q+bPEbteTMH79Hfc1wE7j4+TBDKES0qd16wuNqLgQpFomZjaaZd5fCtH1zNbfjGNnQ8jjZqc5nuucEbHWHhd3GRbuUEuSlF/WbeIqfBCT3+4XyWErWXORYxqKaw3kgWqvZvxWq5WLQtAOHG3CJBDFGNLNmikwkyflp4kz7mIF9MjLmeuq+v/uzvZpR0GhZUfKFfoA9FgkXcEMbFRow==; bm_sv=0DFA928D2CA5F697AF0904ECAA1DB190~YAAQwv1IFx+qoE6OAQAAdMUgUxcmdaHWqdPLmZcUQ9oaWM+klFI06qbbTU8ZlpFJIdC8CpRcQEIswyu9cj4IzaI3gyY5DR0/NNDv8qiBtRnenNLuGTvkwt9HRJaveU2Vch12eu1XPnGHsNIEW8SZDK++x6XuSWi+OYr8m57r9daS4QvY8cPtpRyncEIKjUCOW3EDNQK/KuMsi6jc9UCO4KSdOb7Vgbwf1thm9b/jE4XtHg7+1HOKDDP4fyO+DVA=~1",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "TE": "trailers",
}


def scrape_headlines() -> List[Headline]:
    res: List[Headline] = []

    feed = requests.request("GET", URL, headers=headers, data=payload)

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
            url=url,
            rank=ranking,
        )
        ranking += 1
        res.append(headline)

    return res
