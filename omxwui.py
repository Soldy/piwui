#!/usr/bin/python
import subprocess
import time
import re
import web
from web import form
import os
import pipes
import string

urls = (
'^/$','Interface',
'^/shutdown$','Shutdown',
'^/play/(.*)$','Play',
'^/path/?(.*)$','Path',
'^/playlist/?(.*)$','Playlist',
'^/stop/','Stop',
'^/pause/','Pause',
'^/([^/]*)$','Other'
)

PLAYABLE_TYPES = ['.264','.avi','.bin','.divx','.f4v','.h264','.m4e','.m4v','.m4a','.mkv','.mov','.mp4','.mp4v','.mpe','.mpeg','.mpeg4','.mpg','.mpg2','.mpv','.mpv2','.mqv','.mvp','.ogm','.ogv','.qt','.qtm','.rm','.rts','.scm','.scn','.smk','.swf','.vob','.wmv','.xvid','.x264','.mp3','.flac','.ogg','.wav', '.flv', '.mkv']
MEDIA_RDIR = 'media/'
PAGE_FOLDER = 'omxfront/'
PAGE_NAME = 't.html'
OMXIN_FILE='omxin'

playerstat = {}

playerstat['playing'] = 0
playerstat['pause'] = 0
play_list = []

command_send={
'speedup':'1',
'speeddown':'2',
'nextaudio':'k',
'prevaudio':'j',
'nextchapter':'o',
'prevchapter':'i',
'nextsubs':'m',
'prevsubs':'n',
'togglesubs':'s',
'stop':'q',
'volumedown':'-',
'volumeup':'+',
'languagedown':'j',
'languageup':'k',
'seek-30':'\x1b\x5b\x44',
'seek+30':'\x1b\x5b\x43',
'seek-600':'\x1b\x5b\x42',
'seek+600':'\x1b\x5b\x41'}

class Other:
    def POST(self,name):
        inpury = web.input(kola = 'web')
        print(inpury.kola)
        if not name == '':
            if name in command_send:
                omx_send(command_send[name])
                return '[{\"message\":\"OK\"}]'
            else:
                if os.path.exists(os.path.join(PAGE_FOLDER,name)):
                    page_file = open(os.path.join(PAGE_FOLDER,name),'r')
                    page = page_file.read()
                    page_file.close()
                    return page
                return '[{\"message\":\"FAIL\"}]'
        inpury = web.input(kola = 'web')
        print(inpury.kola)
        print('Incorrect capture!')
        return '[{\"message\":\"ERROR!!!\"}]'

class Pause:
    def POST(self):
        global playerstat
        if playerstat['pause'] == 1:
            omx_send("p")           
            web.header('Content-Type', 'text/json')
            playerstat['pause'] = 0
            return '[{\"message\":\"OK\"},{\"modul\":\"interface\",\"interfac\":\"playing\"}]'
        else:
            omx_send("p")  
            web.header('Content-Type', 'text/json')
            playerstat['pause'] = 1 
            return '[{\"message\":\"OK\"},{\"modul\":\"interface\",\"interfac\":\"pause\"}]'


class Play:
    def POST(self,file):
        global playerstat
        if playerstat['playing'] == 1:
            if playerstat['pause'] == 1:
                omx_send("p")           
                web.header('Content-Type', 'text/json')
                playerstat['pause'] = 0
                return '[{\"message\":\"OK\"},{\"modul\":\"interface\",\"interfac\":\"playing\"}]'
            else:
                omx_send("p")  
                web.header('Content-Type', 'text/json')
                playerstat['pause'] = 1 
                return '[{\"message\":\"OK\"},{\"modul\":\"interface\",\"interfac\":\"pause\"}]'
        else:
            omx_play(file)
            playerstat['playing'] = 1
            web.header('Content-Type', 'text/json')
            return '[{\"message\":\"OK\"},{\"modul\":\"interface\",\"interfac\":\"playing\"}]'

class Stop:
    global playerstat
    def POST(self):
        global playerstat
        if playerstat['playing'] == 1:
           omx_stop()
           playerstat['playing'] = 0
        return '[{\"message\":\"OK\"},{\"modul\":\"interface\",\"interfac\":\"stop\"}]'

class Shutdown:
    def GET(self):
        subprocess.call('/sbin/shutdown -h now',shell=True)
        return '[{\"message\":\"OK\"}]'

class Interface:
    def GET(self):
        page_file = open(os.path.join(PAGE_FOLDER,"ta.html"),'r')
        pagea = page_file.read()
        page_file.close()
        itemlist = []
        path=''
        if path.startswith('..'):
            path = ''
        for item in os.listdir(os.path.join(MEDIA_RDIR,path)):
            if os.path.isfile(os.path.join(MEDIA_RDIR,path,item)):
                fname = os.path.splitext(item)[0]
                fname = re.sub('[^a-zA-Z0-9\[\]\(\)\{\}]+',' ',fname)
                fname = re.sub('\s+',' ',fname)
                fname = string.capwords(fname.strip())
                singletuple = (os.path.join(path,item),fname,'file')
            else:
                fname = re.sub('[^a-zA-Z0-9\']+',' ',item)
                fname = re.sub('\s+',' ',fname)
                fname = string.capwords(fname.strip())
                singletuple = (os.path.join(path,item),fname,'dir')
            itemlist.append(singletuple)
        itemlist = [f for f in itemlist if not os.path.split(f[0])[1].startswith('.')]
        itemlist = [f for f in itemlist if os.path.splitext(f[0])[1].lower() in PLAYABLE_TYPES or f[2]=='dir']
        list.sort(itemlist, key=lambda alpha: alpha[1])
        list.sort(itemlist, key=lambda dirs: dirs[2])
        outputlist=[]
        kar = 0
        for line in itemlist:
            kar+=1
            outputlist.append('singer.playlist['+str(kar)+'] = {\"path\":\"'+line[0]+'\", \"ame\":\"'+line[1]+'\", \"type\":\"'+line[2]+'\"};')
        page_file = open(os.path.join(PAGE_FOLDER,"tb.html"),'r')
        pageb = page_file.read()
        page_file.close()
        web.header('Content-Type', 'text/html')
        return pagea+'\n'.join(outputlist)+pageb
        


class Path:
    def GET(self, path=''):
        itemlist = []
        if path.startswith('..'):
            path = ''
        for item in os.listdir(os.path.join(MEDIA_RDIR,path)):
            if os.path.isfile(os.path.join(MEDIA_RDIR,path,item)):
                fname = os.path.splitext(item)[0]
                fname = re.sub('[^a-zA-Z0-9\[\]\(\)\{\}]+',' ',fname)
                fname = re.sub('\s+',' ',fname)
                fname = string.capwords(fname.strip())
                singletuple = (os.path.join(path,item),fname,'file')
            else:
                fname = re.sub('[^a-zA-Z0-9\']+',' ',item)
                fname = re.sub('\s+',' ',fname)
                fname = string.capwords(fname.strip())
                singletuple = (os.path.join(path,item),fname,'dir')
            itemlist.append(singletuple)
        itemlist = [f for f in itemlist if not os.path.split(f[0])[1].startswith('.')]
        itemlist = [f for f in itemlist if os.path.splitext(f[0])[1].lower() in PLAYABLE_TYPES or f[2]=='dir']
        list.sort(itemlist, key=lambda alpha: alpha[1])
        list.sort(itemlist, key=lambda dirs: dirs[2])
        outputlist=[]
        for line in itemlist:
            outputlist.append('{\"path\":\"'+line[0]+'\", \"name\":\"'+line[1]+'\", \"type\":\"'+line[2]+'\"}')
        return '[\n'+',\n'.join(outputlist)+']'

#This class is not complete yet and only populates the global playlist.
#TO-DO
class Playlist:
   def GET(self, item=''):
       if not item=='':
           play_list.append(item)
       output = '[/n'
       for i, part in enumerate(play_list):
           output = output + '{\"'+i+'\":'+string.capwords(os.path.splitext(part)[0])+'\"}\n'
       output = output + ']'
       return output

if __name__ == "__main__":
    app = web.application(urls,globals())
    app.run()

def omx_send(data):
    subprocess.Popen('echo -n '+data+' >'+re.escape(OMXIN_FILE),shell=True)
    return 1

def omx_play(file):
    #omx_send('q')
    #time.sleep(0.5) #Possibly unneeded - crashing fixed by other means.
    subprocess.Popen('killall -9  omxplayer.bin',stdout=subprocess.PIPE,shell=True)
    subprocess.Popen('clear',stdout=subprocess.PIPE,shell=True)
    subprocess.Popen('omxplayer -p -o hdmi '+os.path.join(MEDIA_RDIR,re.escape(file))+' <'+re.escape(OMXIN_FILE),shell=True)
    omx_send('.')
    return 1


def omx_stop():
    subprocess.Popen('killall -9  omxplayer.bin',stdout=subprocess.PIPE,shell=True)
    subprocess.Popen('clear',stdout=subprocess.PIPE,shell=True)