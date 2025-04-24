from bson import ObjectId

class User:
    def __init__(self, tg_id, nickname, username, coins_count=0, claps_count=0, cat=None, _id=None):
        self.tg_id = tg_id
        self.nickname = nickname
        self.username = username
        self.coins_count = coins_count
        self.claps_count = claps_count
        self.cat = cat
        self._id = _id

    @staticmethod
    def from_mongo(mongo_doc):
        """Конвертирует документ MongoDB в объект User"""
        if not mongo_doc:
            return None
        return User(
            tg_id=mongo_doc.get('tg_id'),
            nickname=mongo_doc.get('nickname'),
            username=mongo_doc.get('username'),
            coins_count=mongo_doc.get('coins_count', 0),
            claps_count=mongo_doc.get('claps_count', 0),
            cat=mongo_doc.get('cat'),
            _id=str(mongo_doc.get('_id'))
        )

    def to_mongo(self):
        """Конвертирует объект User в документ MongoDB"""
        document = {
            'tg_id': self.tg_id,
            'nickname': self.nickname,
            'username': self.username,
            'coins_count': self.coins_count,
            'claps_count': self.claps_count,
            'cat': self.cat
        }
        if self._id:
            document['_id'] = ObjectId(self._id)
        return document
