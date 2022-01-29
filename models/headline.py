from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib
from typing import List


@dataclass
class Headline:
    title: str
    summary: str
    url: str
    datetime: str = datetime.now().isoformat()
    id: str = ""

    def __post_init__(self):
        self.id = create_unique_id(self.title)

    def as_dict(self):
        return asdict(self)


def create_unique_id(title: str):
    return hashlib.md5(title.encode("utf-8")).hexdigest()
