from sqlalchemy import Column, Integer, String, Sequence, ForeignKey
from sqlalchemy.orm import relationship

from .database import Base, session

class Song(Base):
    __tablename__ = 'songs'
    id = Column(Integer, primary_key = True)

    file = relationship("File", uselist=False, backref="song")

    def as_dictionary(self):
        song = {
            "id": self.id,
            "file":
                {"file_id":self.file.id,
                 "file_name": self.file.name}
        }
        return song

class File(Base):
    __tablename__ = 'files'

    id = Column(Integer, primary_key=True)
    name = Column(String(128))

    song_id = Column(Integer, ForeignKey('songs.id'),nullable=False)

    def as_dictionary(self):
        file = {
            "id": self.id,
            "name": self.name
        }
        return file