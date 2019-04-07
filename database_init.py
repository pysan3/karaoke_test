import os
from glob import glob
from datetime import datetime

from run_main import functions, logger
import apps.app as backapp
from apps.database import Base, engine, Session, Eventnames, Eventlogs, Musics, Users

def delete_music():
    for k in ['wav', 'vocal', 'inst']:
        audio_list = glob('./audio/{0}/[0-9]*.wav'.format(k))
        print(audio_list)
        for audio in audio_list:
            os.remove(audio)

def create_new_database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

def init_db():
    session = Session()
    create_eventnames()
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
    logger.info('{0}@_@{1} {2} {3} {4}'.format(
        0, 9, 0, 1, 0
    ))
    session.commit()
    session.close()

def create_eventnames():
    session = Session()
    names =  session.query(Eventnames).all()
    for func in functions:
        if func not in names:
            session.add(Eventnames(event_name=func))
    session.commit()
    session.close()

create_new_database()
init_db()
delete_music()