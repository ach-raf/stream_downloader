from dataclasses import dataclass


@dataclass
class RedditGoal:
    id: str
    title: str
    url: str
    direct_url: str
    created_utc: int
