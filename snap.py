import json
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class ItemList:
    type_str: str
    upload_time: str
    url: str
    viewcount: int
    username: str
    duration: str
    width: str
    height: str
    encoding_format: str
    #snap_id: str
    #url: str
    #create_time: str
    #file_type: str
    #locale: str
    #duration: str
    #snapMediaInfo: str


class ItemListJSONEncoder(json.JSONEncoder):
    def default(self, o: ItemList):
        return asdict(o)


@dataclass
class userProfile:
    username: str
    title: str
    snapcodeImageUrl: str
    badge: int=0
    categoryStringId: str=""
    subscriberCount: int=0
    bio: str=""
    websiteurl: str=""
    profile_url: str=""
    address: str=""

class userProfileJSONEncoder(json.JSONEncoder):
    def default(self, o: userProfile):
        return asdict(o)

@dataclass
class story:
    snapIndex: int
    snapID: str
    url: str
    upload_time: str


class storyJSONEnconder(json.JSONEncoder):
    def default(self, o: story):
        return asdict(o)


@dataclass
class spotlight:
    storyId: str
    storyTitle: str
    snapList: list
    snapList_len: int

class spotlightJSONEncoder(json.JSONEncoder):
    def default(self, o:spotlight):
        return asdict(o)