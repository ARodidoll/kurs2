from bson import ObjectId

class Cat:
    def __init__(self, cat_id, cat_img, _id=None):
        self.cat_id = cat_id
        self.cat_img = cat_img
        self._id = _id

    @staticmethod
    def from_mongo(mongo_doc):
        """Конвертирует документ MongoDB в объект Cat"""
        if not mongo_doc:
            return None
        return Cat(
            cat_id=mongo_doc.get('cat_id'),
            cat_img=mongo_doc.get('cat_img'),
            _id=str(mongo_doc.get('_id'))
        )

    def to_mongo(self):
        """Конвертирует объект Cat в документ MongoDB"""
        document = {
            'cat_id': self.cat_id,
            'cat_img': self.cat_img
        }
        if self._id:
            document['_id'] = ObjectId(self._id)
        return document
