from pydantic import BaseModel, Extra, validator
from datetime import datetime
import hashlib
from typing import Optional


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
