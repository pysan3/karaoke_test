import responder
import sqlite3

import os
import sys
import json
import io
import cgi
from random import randint
from time import sleep

import apps.app as backapp
import audio.music as backmusic

backapp.set_templates()
api = responder.API(templates_dir='static')
api.add_route('/', static=True, websocket=True)
logger = backapp.create_logger(__name__)
# logger.info(msg@_@event_id, user_id, post, result)

functions = [
    'index',
    'random_number',
    'loggedin',
    'login',
    'signup',
    'logout',
    'musiclist',
    'upload',
    'load_music',
    'ws_sing'
]

# @api.route('/')
# async def index(req, resp):
#     f_index = functions.index(sys._getframe().f_code.co_name)
#     logger.info('@{0} {1} _ index.html'.format(0, f_index))
#     resp.content = api.template('index.html')

@api.route('/api/login')
async def login(req, resp):
    f_index = functions.index(sys._getframe().f_code.co_name)
    user = await req.media()
    # {'user_name': '', 'user_password': ''}
    result = backapp.login(user)
    # {'user_id':user_id, 'msg':msg}
    logger.info('{0}@_@{1} {2} {3} {4}'.format(
        result['msg'], f_index, result['user_id'], user['user_name'], (result['user_id'] != -1)
    ))
    resp.media = result

@api.route('/api/logout')
async def logout(req, resp):
    f_index = functions.index(sys._getframe().f_code.co_name)
    user_id = await req.text
    logger.info('{0}@_@{1} {2} {3} {4}'.format(
        'logout', f_index, user_id, 'logout request', 1
    ))
    resp.text = '1'

@api.route('/api/loggedin/{user_id}')
async def loggedin(req, resp, *, user_id):
    f_index = functions.index(sys._getframe().f_code.co_name)
    result = backapp.logged_in(int(user_id))
    # result = 1 / 0
    logger.info('{0}@_@{1} {2} {3} {4}'.format(
        '' if result else 'not ' + 'logged in', f_index, user_id, user_id, result
    ))
    resp.text = str(result)

@api.route('/api/signup')
async def signup(req, resp):
    f_index = functions.index(sys._getframe().f_code.co_name)
    user = await req.media()
    # {'user_name': '', 'user_password': ''}
    result = backapp.signup(user)
    # {'user_id':user_id, 'msg':msg}
    logger.info('{0}@_@{1} {2} {3} {4}'.format(
        result['msg'], f_index, result['user_id'], user['user_name'], (result['user_id'] != -1)
    ))
    resp.media = result

@api.route('/api/musiclist')
async def musiclist(req, resp):
    f_index = functions.index(sys._getframe().f_code.co_name)
    result = backapp.music_list()
    # {['id':num, name':'song_title', 'singer':'singer_name', 'count':num], ...}
    logger.info('{0}@_@{1} {2} {3} {4}'.format(
        'success', f_index, 0, '', 'list of musics'
    ))
    resp.media = json.dumps(result)

@api.route('/api/upload')
async def upload(req, resp):
    # TODO: return song_id if music already exists
    f_index = functions.index(sys._getframe().f_code.co_name)
    data = cgi.FieldStorage(fp=io.BytesIO(await req.content), environ={'REQUEST_METHOD':'POST'}, headers=req.headers).list
    # ['user_id', 'song_title', 'singer', 'file_type', 'data']
    song_id = backapp.add_music(data[1].value, data[2].value)
    if song_id != -1:
        @api.background.task
        def music_upload(song_id, data, ftype):
            if not backmusic.upload(song_id, data, ftype):
                logger.info('{0}@_@{1} {2} {3} {4}'.format(
                    'music hash failed', f_index, 0, song_id, 0
                ))
                return
            h, t, n = backmusic.upload_hash(song_id)
            backapp.upload_hash(song_id, h, t, n)
            logger.info('{0}@_@{1} {2} {3} {4}'.format(
                'music hashed', f_index, 0, song_id, len(h.split())
            ))
        logger.info('{0}@_@{1} {2} {3} {4}'.format(
            'music upload', f_index, data[0].value, song_id, 1
        ))
        music_upload(song_id, data[4].value, data[3].value)
    resp.media = {'song_id':song_id}

@api.route('/api/alreadyExists')
async def alreadyExists(req, resp):
    data = await req.media()
    song_id = backapp.isExist(data['song_title'], data['singer'])
    resp.media = {'song_id':song_id}

@api.route('/api/isUploaded/{song_id}')
async def isUploaded(req, resp, *, song_id):
    resp.media = {'isUploaded':backapp.finish_upload(song_id)}

@api.route('/audio/load_music/{req_id}')
async def load_music(req, resp, *, req_id):
    f_index = functions.index(sys._getframe().f_code.co_name)
    user_id = req_id.split('_')[0]
    song_id = req_id.split('_')[1]
    result = backmusic.load_music(song_id, 'inst')
    # {'song_id':song.id, 'name':song.song_title, 'singer':song.singer}
    if result == False:
        resp.status_code = 500
        return
    logger.info('{0}@_@{1} {2} {3} {4}'.format(
        'music_request', f_index, user_id, song_id, 1
    ))
    resp.content = result

@api.route('/ws/sing', websocket=True)
async def ws_sing(ws):
    f_index = functions.index(sys._getframe().f_code.co_name)
    @api.background.task
    def lag_estimate(handler):
        handler.lag_estimate()
        handler.noise_reduction()
    await ws.accept()
    data = await ws.receive_json()
    ws_handler = backmusic.WebSocketApp(backapp.hashtable(data['song_id']))
    while True:
        try:
            ws_handler.upload(await ws.receive_bytes())
            if ws_handler.counter[0] == 50 * 5:
                lag_estimate(ws_handler)
        except:
            ws_handler.close(data)
            break
    logger.info('{0}@_@{1} {2} {3} {4}'.format(
        'ws connection completed', f_index, data['user_id'], data['song_id'], ws_handler.return_counter()
    ))

@api.route('/api/random')
def random_number(req, resp):
    f_index = functions.index(sys._getframe().f_code.co_name)
    result = {'randomNumber': randint(1, 100)}
    logger.info('{0}@_@{1} {2} {3} {4}'.format(
        'randomNumber request', f_index, 0, '', result['randomNumber']
    ))
    resp.media = result

if __name__ == '__main__':
    api.run(address='0.0.0.0')
