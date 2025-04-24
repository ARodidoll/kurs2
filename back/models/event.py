from bson import ObjectId
from datetime import datetime

class Event:
    def __init__(self, title, description, start_date, end_date, location, max_participants=None, _id=None):
        self.title = title
        self.description = description
        self.start_date = start_date
        self.end_date = end_date
        self.location = location
        self.max_participants = max_participants
        self._id = _id

    @staticmethod
    def from_mongo(mongo_doc):
        """Конвертирует документ MongoDB в объект Event"""
        if not mongo_doc:
            return None
        return Event(
            title=mongo_doc.get('title'),
            description=mongo_doc.get('description'),
            start_date=mongo_doc.get('start_date'),
            end_date=mongo_doc.get('end_date'),
            location=mongo_doc.get('location'),
            max_participants=mongo_doc.get('max_participants'),
            _id=str(mongo_doc.get('_id'))
        )

    def to_mongo(self):
        """Конвертирует объект Event в документ MongoDB"""
        document = {
            'title': self.title,
            'description': self.description,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'location': self.location,
            'max_participants': self.max_participants
        }
        if self._id:
            document['_id'] = ObjectId(self._id)
        return document
