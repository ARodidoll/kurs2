from bson import ObjectId

class Participant:
    def __init__(self, name, email, phone, events=None, _id=None):
        self.name = name
        self.email = email
        self.phone = phone
        self.events = events or []
        self._id = _id

    @staticmethod
    def from_mongo(mongo_doc):
        """Конвертирует документ MongoDB в объект Participant"""
        if not mongo_doc:
            return None
        return Participant(
            name=mongo_doc.get('name'),
            email=mongo_doc.get('email'),
            phone=mongo_doc.get('phone'),
            events=mongo_doc.get('events', []),
            _id=str(mongo_doc.get('_id'))
        )

    def to_mongo(self):
        """Конвертирует объект Participant в документ MongoDB"""
        document = {
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'events': self.events
        }
        if self._id:
            document['_id'] = ObjectId(self._id)
        return document
