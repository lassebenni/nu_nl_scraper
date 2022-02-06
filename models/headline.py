import json
from pydantic import BaseModel, Extra, validator
from datetime import datetime
import hashlib
from typing import Dict, List, Optional


class Headline(BaseModel, extra=Extra.allow):
    title: str
    summary: str
    link: Optional[str] = ""
    url: str = ""
    datetime: str = datetime.now().isoformat()
    id: str = ""

    @validator("url", pre=True)
    def set_url(cls, v, values):
        if v:
            return v
        else:
            return values["link"]

    @validator("id", pre=True)
    def set_id(cls, v, values):
        return create_unique_id(values["title"])


def create_unique_id(title: str):
    return hashlib.md5(title.encode("utf-8")).hexdigest()


def drop_duplicates(headlines: List[Headline]) -> List[Headline]:
    unique_headlines: List[Headline] = []
    unique_ids = []

    for headline in headlines:
        if not headline.id and headline.title:
            headline.id = create_unique_id(headline.title)

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
    prev_headlines = read_previous_headlines(path)
    headlines = drop_duplicates(headlines + prev_headlines)

    with open(path, "w") as f:
        if as_json:
            headline_dicts: List[Dict] = [headline.dict() for headline in headlines]

        f.write(json.dumps(headline_dicts, default=str))
