from __future__ import absolute_import, division, print_function, unicode_literals
import logging
from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

__version__ = "0.1.0"

engine = create_engine('sqlite:///apps/database.sqlite3', echo=False)
Base = declarative_base()

Session = sessionmaker(bind=engine)

class Eventlogs(Base):
	__tablename__ = 'eventlogs'
	id = Column('id', Integer, primary_key=True)
	asctime = Column('asctime', String)
	log_name = Column('log_name', String)
	levelno = Column('levelno', Integer)
	user_id = Column('user_id', Integer)
	event_id = Column('event_id', Integer)
	push = Column('push', String)
	result = Column('result', String)
	log_message = Column('log_message', String)

	def __repr__(self):
		return '<Eventlogs(id=%s, asctime=%s, log_name=%s, levelno=%s, user_id=%s, event_id=%s, push=%s, result=%s, log_message=%s, )>' \
			% (self.id, self.asctime, self.log_name, self.levelno, self.user_id, self.event_id, self.push, self.result, self.log_message)

class Eventnames(Base):
	__tablename__ = 'eventnames'
	id = Column('id', Integer, primary_key=True)
	event_name = Column('event_name', String)

	def __repr__(self):
		return '<Eventnames(id=%s, event_name=%s, )>' \
			% (self.id, self.event_name)

class Users(Base):
	__tablename__ = 'users'
	id = Column('id', Integer, primary_key=True)
	user_name = Column('user_name', String)
	user_password = Column('user_password', String)
	created_at = Column('created_at', String)

	def __repr__(self):
		return '<Users(id=%s, user_name=%s, user_password=%s, created_at=%s, )>' \
			% (self.id, self.user_name, self.user_password, self.created_at)

class Musics(Base):
    __tablename__ = 'musics'
    id = Column('id', Integer, primary_key=True)
    song_title = Column('song_title', String)
    singer = Column('singer', String)
    created_at = Column('created_at', String)

    def __repr__(self):
        return '<Musics(id=%s, song_title=%s, singer=%s, created_at=%s, )>' \
            % (self.id, self.song_title, self.singer, self.created_at)

class Hsh(Base):
    __tablename__ = 'hsh'
    id = Column('id', Integer, primary_key=True)
    song_id = Column('song_id', Integer)
    hsh_data = Column('hsh_data', String)
    ptime = Column('ptime', String)
    noise = Column('noise', Integer)

    def __repr__(self):
        return '<Hsh(id=%s, song_id=%s, hsh_data=%s, ptime=%s, noise=%s, )>' \
            % (self.id, self.song_id, self.hsh_data, self.ptime, self.noise)

class SQLiteHandler(logging.Handler):
    def __init__(self):
        logging.Handler.__init__(self)
        session = Session()
        session.commit()
        session.close()

    def _rec(self, record):
        record.asctime = datetime.now().isoformat(' ', 'seconds')
        if '@_@' in record.msg:
            i = record.msg.index('@_@')
            message = record.msg[:i]
            record.msg = record.msg[i+2:]
        else:
            message = record.msg
        if record.msg[0] != '@':
            record.user_id = 0
            record.event_id = 0
            record.push = ''
            record.result = ''
        else:
            recs = record.msg[1:].split(' ')
            record.user_id = int(recs[0])
            record.event_id = int(recs[1])
            record.push = recs[2]
            record.result = recs[3]
        record.msg = message
        return record

    def emit(self, record):
        sql = "INSERT INTO eventlogs (asctime, log_name, levelno, log_message, user_id, event_id, push, result) VALUES\
         ('%(asctime)s', '%(name)s', '%(levelno)s', '%(msg)s', '%(user_id)s', '%(event_id)s', '%(push)s', '%(result)s')"
        record = self._rec(record)
        session = Session()
        session.execute(sql % record.__dict__)
        session.commit()
        session.close()

if __name__ == '__main__':
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    session = Session()
    session.add(Users(
        user_name='master',
        user_password='password',
        created_at=datetime.now().isoformat(' ', 'seconds'),
    ))
    session.add(Musics(
        song_title='wonder stella',
        singer='fhana',
        created_at=datetime.now().isoformat(' ', 'seconds'),
    ))
    session.commit()
    session.close()