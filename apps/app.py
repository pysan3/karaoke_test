import numpy as np
import logging
import hashlib
import os
import collections
import statistics
from datetime import datetime

from apps.database import Session, Eventlogs, Eventnames, Users, Musics, Hsh, SQLiteHandler

def login(data):
    session = Session()
    user = session.query(Users).filter_by(user_name=data['user_name']).all()
    session.close()
    user_id = -1
    password = hashlib.sha256(data['user_password'].encode()).hexdigest()
    if len(user) == 1:
        if user[0].user_password == password:
            msg = 'success'
            user_id = user[0].id
        else:
            msg = 'wrong password'
    else:
        msg = 'wrong username'
    return {'isFound': len(user), 'user_id': user_id, 'msg': msg}

def signup(data):
    name = data['user_name']
    user_id = -1
    session = Session()
    user = session.query(Users).filter_by(user_name=name).all()
    if len(user) == 0:
        user_id = session.query(Users).count() + 1
        session.add(Users(
            user_name=name,
            user_password=hashlib.sha256(data['user_password'].encode()).hexdigest(),
            created_at=datetime.now().isoformat(' ', 'seconds')
        ))
        session.commit()
        msg = 'succeeded to create an user account'
    else:
        msg = 'already exists'
    session.close()
    return {'user_id': user_id, 'msg': msg}

def logged_in(user_id):
    if user_id < 2:
        return 0
    session = Session()
    result = session.query(Eventlogs).filter_by(user_id=user_id).all()
    event_id_logout = session.query(Eventnames).filter_by(event_name='logout').one().id - 1
    session.close()
    if len(result) == 0 or result[-1].event_id == event_id_logout:
        return 0
    else:
        return 1

def music_list():
    session = Session()
    songs = session.query(Musics).all()
    event_id_ws_sing = session.query(Eventnames).filter_by(event_name='ws_sing').one().id - 1
    count = session.query(Eventlogs).filter_by(event_id=event_id_ws_sing).all()
    session.close()
    song_dict = collections.defaultdict(int)
    for i in range(len(count)):
        song_dict[int(count[i].push)] += 1
    result = sorted([[song.id, song.song_title, song.singer, song_dict[int(song.id)]] for song in songs], key=lambda x:x[3], reverse=True)
    return result

def isExist(name, singer):
    session = Session()
    song = session.query(Musics).filter_by(song_title=name, singer=singer).all()
    session.close()
    if len(song):
        return song[0].id
    else:
        return 0

def add_music(name, singer):
    session = Session()
    song_id = session.query(Musics).count() + 1
    session.add(Musics(
        song_title=name,
        singer=singer,
        created_at=datetime.now().isoformat(' ', 'seconds'),
    ))
    session.commit()
    session.close()
    return song_id

def upload_hash(song_id, h, t, n):
    # TODO: format table?
    session = Session()
    session.add(Hsh(
        song_id=song_id,
        hsh_data=h,
        ptime=t,
        noise=n
    ))
    session.commit()
    session.close()

def ws_lag():
    session = Session()
    event_id_ws_sing = session.query(Eventnames).filter_by(event_name='ws_sing').one().id - 1
    lag_list = session.query(Eventlogs).filter_by(event_id=event_id_ws_sing).all()
    session.close()
    lag = statistics.median([int(l.log_message) for l in lag_list])
    return lag

def hashtable(song_id):
    session = Session()
    hsh = session.query(Hsh).filter_by(song_id=song_id).one()
    session.close()
    return hsh.hsh_data, hsh.ptime, hsh.noise

def finish_upload(song_id):
    session = Session()
    res = session.query(Hsh).filter_by(song_id=song_id).all()
    session.close()
    return len(res)

def create_logger(filename):
    logger = logging.getLogger(filename)
    fmt = '%(name)s %(levelno)s %(funcName)s %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=fmt)
    logger.setLevel(logging.DEBUG)
    # -> /co logger
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    logger.addHandler(stream_handler)
    # till here
    sqlite_handler = SQLiteHandler()
    sqlite_handler.setLevel(logging.DEBUG)
    logger.addHandler(sqlite_handler)
    logger.propagate = False
    return logger

def set_templates():
    import shutil
    path_name = 'static/'
    for s in next(os.walk(path_name*2))[1]:
        shutil.move(path_name*2+s, path_name+s)
    if os.path.isfile(path_name + 'favicon.ico'):
        shutil.move(path_name + 'favicon.ico', 'favicon.ico')