from datetime import datetime
import hashlib

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


class Post(Base):
    __tablename__ = 'posts'

    id = Column(Integer, primary_key=True)
    subject = Column(String(50))
    comment = Column(String(120))
    filename = Column(String(100))
    mimetype = Column(String(100))
    bytes = Column(Integer)

    created = Column(DateTime, default=datetime.utcnow)
    parent_id = Column(Integer, ForeignKey('posts.id'))

    children = relationship("Post",
                            lazy="joined",
                            join_depth=1)


    def __init__(self, subject, comment, parent_id):
        self.subject = subject
        self.comment = comment
        self.parent_id = parent_id

    def __repr__(self):
        return "{0} {1}".format(self.subject, self.comment)

    def generate_filename(self):
        m = hashlib.md5()
        m.update(str(self.id))
        m.update(self.subject)
        m.update(self.comment)
        return m.hexdigest()[0:16]