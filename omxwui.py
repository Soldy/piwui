#!/usr/bin/python
import subprocess
import time
import re
import web
import os
import string
import pexpect
import distutils.spawn
import logging
import math
import threading


urls = (
'^/$','Getco',
'^/([^/]*)$','Other'
)



PLAYABLE_TYPES = ['.264','.avi','.bin','.divx','.f4v','.h264','.m4e','.m4v','.m4a','.mkv','.mov','.mp4','.mp4v','.mpe','.mpeg','.mpeg4','.mpg','.mpg2','.mpv','.mpv2','.mqv','.mvp','.ogm','.ogv','.qt','.qtm','.rm','.rts','.scm','.scn','.smk','.swf','.vob','.wmv','.xvid','.x264','.mp3','.flac','.ogg','.wav', '.flv', '.mkv']
MEDIA_RDIR = 'media/'
PAGE_FOLDER = 'omxfront/'
PAGE_NAME = 't.html'

playerstat = {}

playerstat['playing'] = 0
playerstat['pause'] = 0
playerstat['outtags'] = 0
playerstat['outtage'] = 0
playerstat['played'] = "none"
play_list = {}
play_list['id'] = []
play_list['title'] = []
play_list['path'] = [] 
play_list['filename'] = []
play_list['format'] = []
play_list['toplist']=[]
play_list['length']=[]


outputlist=[]



logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

_OMXPLAYER_EXECUTABLE = "/usr/bin/omxplayer"

def is_omxplayer_available():
    """
:rtype: boolean
"""
    return distutils.spawn.find_executable(_OMXPLAYER_EXECUTABLE) is not None

class OMXPlayerinfo(object):
    _LENGTH_REXP = re.compile(r".*Duration:\s*(\W.+), start.*")
    _LAUNCH_CMD = _OMXPLAYER_EXECUTABLE + " -i %s %s"
    def __init__(self, mediafile, args=None, start_playback=True):
        self.mediafile = mediafile
        if not args:
            args = ""
        cmd = self._LAUNCH_CMD % (mediafile, args)
        self._process = pexpect.spawn(cmd)
        while True:
            line = self._process.readline()
            if line != '':
                m = self._LENGTH_REXP.match(line)
                if m:
                    mfull = m.group(1)
                    movieleng = re.split('[:\D]+',mfull)
                    self.movielength=(int(movieleng[10])*3600)+(int(movieleng[11])*60)+(int(movieleng[12]))
            else:
                break 

class OMXPlayer(object):

    _FILEPROP_REXP = re.compile(r".*audio streams (\d+) video streams (\d+) chapters (\d+) subtitles (\d+).*")
    _VIDEOPROP_REXP = re.compile(r".*Video codec ([\w-]+) width (\d+) height (\d+) profile (\d+) fps ([\d.]+).*")
    _AUDIOPROP_REXP = re.compile(r"Audio codec (\w+) channels (\d+) samplerate (\d+) bitspersample (\d+).*")
    _STATUS_REXP = re.compile(r"V :\s*([\d.]+).*")
    _DONE_REXP = re.compile(r"have a nice day.*")

    _LAUNCH_CMD = _OMXPLAYER_EXECUTABLE + " -o hdmi -s %s %s"

    _PAUSE_CMD = 'p'
    _TOGGLE_SUB_CMD = 's'
    _QUIT_CMD = 'q'
    _DECREASE_VOLUME_CMD = '-'
    _INCREASE_VOLUME_CMD = '+'
    _DECREASE_SPEED_CMD = '1'
    _INCREASE_SPEED_CMD = '2'
    _SEEK_BACKWARD_30_CMD = "\033[D" # key left
    _SEEK_FORWARD_30_CMD = "\033[C" # key right
    _SEEK_BACKWARD_600_CMD = "\033[B" # key down
    _SEEK_FORWARD_600_CMD = "\033[A" # key up

    _VOLUME_INCREMENT = 0.5 # Volume increment used by OMXPlayer in dB

    # Supported speeds.
    # OMXPlayer supports a small number of different speeds.
    SLOW_SPEED = -1
    NORMAL_SPEED = 0
    FAST_SPEED = 1
    VFAST_SPEED = 2

    def __init__(self, mediafile, args=None, start_playback=True):
        self.mediafile = mediafile
        if not args:
            args = ""
        cmd = self._LAUNCH_CMD % (mediafile, args)
        self._process = pexpect.spawn(cmd)

        self._paused = False
        self._subtitles_visible = True
        self._volume = 0 # dB
        self._speed = self.NORMAL_SPEED
        self.position = 0.0

        self._position_thread = threading.Thread(target=self._get_position)
        self._position_thread.start()

        if not start_playback:
            self.toggle_pause()
        self.toggle_subtitles()


    def _get_position(self):
        while True:
            index = self._process.expect([self._STATUS_REXP,
                                            pexpect.TIMEOUT,
                                            pexpect.EOF,
                                            self._DONE_REXP])
            if index == 1: continue
            elif index in (2, 3): break
            else:
                self.position = float(self._process.match.group(1))
            time.sleep(0.05)

    def toggle_pause(self):
        if self._process.send(self._PAUSE_CMD):
            self._paused = not self._paused

    def toggle_subtitles(self):
        if self._process.send(self._TOGGLE_SUB_CMD):
            self._subtitles_visible = not self._subtitles_visible

    def stop(self):
        self._process.send(self._QUIT_CMD)
        self._process.terminate(force=True)

    def decrease_speed(self):
        """
Decrease speed by one unit.
"""
        self._process.send(self._DECREASE_SPEED_CMD)

    def increase_speed(self):
        """
Increase speed by one unit.
"""
        self._process.send(self._INCREASE_SPEED_CMD)

    def set_speed(self, speed):
        """
Set speed to one of the supported speed levels.

OMXPlayer does not support granular speed changes.
"""
        logger.info("Setting speed = %s" % speed)

        assert speed in (self.SLOW_SPEED, self.NORMAL_SPEED, self.FAST_SPEED, self.VFAST_SPEED)

        changes = speed - self._speed
        if changes > 0:
            for i in range(1,changes):
                self.increase_speed()
        else:
            for i in range(1,-changes):
                self.decrease_speed()
        self._speed = speed

    def set_audiochannel(self, channel_idx):
        raise NotImplementedError

    def set_subtitles(self, sub_idx):
        raise NotImplementedError

    def set_chapter(self, chapter_idx):
        raise NotImplementedError

    def set_volume(self, volume):
        """
Set volume to `volume` dB.
"""
        logger.info("Setting volume = %s" % volume)

        volume_change_db = volume - self._volume
        if volume_change_db != 0:
            changes = int( round( volume_change_db / self._VOLUME_INCREMENT ) )
            if changes > 0:
                for i in range(1,changes):
                    self.increase_volume()
            else:
                for i in range(1,-changes):
                    self.decrease_volume()
                    
        self._volume = volume

    def seek(self, offset):
        """
mountainpenguin's hack:
stop player, and restart at a specific point using the -l flag (position)
"""
        logger.info("Stopping omxplayer")
        self.stop()
        logger.info("Restarting at offset %s" % offset)
        self.__init__(mediafile=self.mediafile, args="-l %s" % offset)
        return

        """
Seek to offset seconds into the video.

Greater granulity OMXPlayer provides is 30 seconds so will seek to nearest.

Basic implementation, does not check duration when seeking forward.
"""
        logger.info("Seeking to target offset = %s" % offset)
        curr_offset = self.position / 1000 / 1000
        large_seeks, small_seeks = self._calculate_num_seeks(curr_offset, offset)
        logger.info("Seeking to actual offset = %s" % str(curr_offset + large_seeks*600 + small_seeks*30))
        sleep_time = 0.7
        if large_seeks != 0:
            if large_seeks > 0:
                for i in range(large_seeks):
                    self.seek_forward_600()
                    time.sleep(sleep_time)
            else:
                for i in range(-large_seeks):
                    self.seek_backward_600()
                    time.sleep(sleep_time)
        if small_seeks != 0:
            if small_seeks > 0:
                for i in range(small_seeks):
                    self.seek_forward_30()
                    time.sleep(sleep_time)
            else:
                for i in range(-small_seeks):
                    self.seek_backward_30()
                    time.sleep(sleep_time)
    
    @classmethod
    def _calculate_num_seeks(cls, curr_offset, target_offset):
        diff = target_offset - curr_offset
        large_seeks = int(math.floor(diff / 600.0))
        diff -= large_seeks*600
        small_seeks = int(math.floor(diff / 30.0))
        return large_seeks, small_seeks

    def seek_forward_30(self):
        self._process.send(self._SEEK_FORWARD_30_CMD)

    def seek_forward_600(self):
        self._process.send(self._SEEK_FORWARD_600_CMD)

    def seek_backward_30(self):
        self._process.send(self._SEEK_BACKWARD_30_CMD)

    def seek_backward_600(self):
        """
Seeks backward by 600 seconds.
"""
        self._process.send(self._SEEK_BACKWARD_600_CMD)

    def decrease_volume(self):
        """
Decrease volume by one unit. See `_VOLUME_INCREMENT`.
"""
        self._volume -= self._VOLUME_INCREMENT
        self._process.send(self._DECREASE_VOLUME_CMD)

    def increase_volume(self):
        """
Increase volume by one unit. See `_VOLUME_INCREMENT`.
"""
        self._volume += self._VOLUME_INCREMENT
        self._process.send(self._INCREASE_VOLUME_CMD)


class Getco:
    def POST(self):
        global omx
        inpury = web.input(command = 'web')
        if inpury.command=="play":
            inpuy = web.input(fil = 'web')
            omx_play(str(inpuy.fil))
        elif inpury.command=="stop":
            omx_stop()
        elif inpury.command=="pause":
            omx_pause()
        elif inpury.command=="seek+30'":
            omx.seek_forward_30()
        elif inpury.command=="seek-30'":
            omx.seek_backward_30()
        else:
            return "[{"+omx_status()+"},"+','.join(outputlist)+"]"
        return "[{"+omx_status()+"}]"
    def GET(self):
        page_file = open(os.path.join(PAGE_FOLDER,"t.html"),'r')
        pagea = page_file.read()
        page_file.close()
        web.header('Content-Type', 'text/html')
        return pagea

def omx_send(data):
    subprocess.Popen('echo -n '+data+' >'+re.escape(OMXIN_FILE),shell=True)
    return 1

def omx_play(file):
    global playerstat
    global play_list
    global omx
    #omx_send('q')
    #time.sleep(0.5) #Possibly unneeded - crashing fixed by other means.
    if playerstat['playing'] == 1:
        omx_pause()
    else: 
        omx.stop()
        time.sleep(1)
        playerstat['playing']=1
        playerstat['played'] =str(file)
        omx = OMXPlayer(os.path.join(MEDIA_RDIR,re.escape(play_list['path'][play_list['id'].index(str(file))])))
    return 1

def omx_playlist():
        global outputlist
        global play_list
        global omxinfo
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
        play_list['toplist'] = []
        for line in itemlist:
            if line[1] not in play_list['filename']: 
                play_list['toplist'].append(str(len(play_list['id'])))
                play_list['id'].append(str(len(play_list['id'])))
                play_list['path'].append(line[0])
                play_list['filename'].append(line[1])
                play_list['format'].append(line[2])
                omxinfo =  OMXPlayerinfo(os.path.join(MEDIA_RDIR,re.escape(line[0])))
                play_list['length'].append(omxinfo.movielength)
            else:
                play_list['toplist'].append(str(play_list['filename'].index(line[1])))
            outputlist.append('{\"id\":\"'+str(play_list['filename'].index(line[1]))+'\",\"modul\":\"playlist\",\"path\":\"'+line[0]+'\", \"nam\":\"'+line[1]+'\", \"type\":\"'+line[2]+'\", \"lengt\":\"'+str(play_list['length'][play_list['filename'].index(line[1])])+'\"}')


def omx_stop():
    global playerstat
    global omx
    omx.stop()
    playerstat['pause']=0
    playerstat['playing']=0
    playerstat['played'] = "none"
    
def omx_pause():
    global playerstat
    global omx
    if playerstat['pause'] == 0 and playerstat['playing'] == 1:
       playerstat['pause']=1
       omx.toggle_pause()
    elif playerstat['pause'] == 1 and playerstat['playing'] == 1:
       playerstat['pause']=0
       omx.toggle_pause()
    return 1
        
def omx_status():
    global playerstat
    global omx
    if playerstat['pause'] == 1:
        return '\"modul\":\"interface\",\"interfac\":\"pause\",\"singed\":\"'+playerstat['played']+'\",\"position\":\"'+str(omx.position)+'\"'
    elif playerstat['playing'] == 1:
        return '\"modul\":\"interface\",\"interfac\":\"playing\",\"singed\":\"'+playerstat['played']+'\",\"position\":\"'+str(omx.position)+'\"'
    else:
        return '\"modul\":\"interface\",\"interfac\":\"stop\",\"singed\":\"'+playerstat['played']+'\",\"position\":\"'+str(omx.position)+'\"'
        


omx = OMXPlayer('')
omxinfo =  OMXPlayerinfo('')
        
omx_playlist()
print '\n'.join(outputlist)

if __name__ == "__main__":
    app = web.application(urls,globals())
    web.config.debug = False
    app.run()