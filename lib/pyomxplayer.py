import pexpect
import re
import distutils.spawn
import logging
import math
import time
import threading

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
                    self.movielengthur=movieleng[10]
                    self.movielengtmun=movieleng[11]
                    self.movielengtsuc=movieleng[12]
                    self.movielength=(int(movieleng[10])*3600)+(int(movieleng[11])*60)+(int(movieleng[12]))
            else:
                break

"""
        cmd = self._LAUNCH_CMD % (mediafile, args)
        self._process = pexpect.spawn(cmd)
        self.movielength = self._LENGTH_REXP.match('Duration: 00:00:00.00, start 00').group(1)
"""     

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
        
        # Video and audio property detection code is not functional.
        # Don't need this so remove for the moment.
        
# self.video = dict()
# self.audio = dict()
# # Get file properties
# file_props = self._FILEPROP_REXP.match(self._process.readline()).groups()
# (self.audio['streams'], self.video['streams'],
# self.chapters, self.subtitles) = [int(x) for x in file_props]
# # Get video properties
# video_props = self._VIDEOPROP_REXP.match(self._process.readline()).groups()
# video_props = self._VIDEOPROP_REXP.match(s).groups()
# self.video['decoder'] = video_props[0]
# self.video['dimensions'] = tuple(int(x) for x in video_props[1:3])
# self.video['profile'] = int(video_props[3])
# self.video['fps'] = float(video_props[4])
# # Get audio properties
# audio_props = self._AUDIOPROP_REXP.match(self._process.readline()).groups()
# self.audio['decoder'] = audio_props[0]
# (self.audio['channels'], self.audio['rate'],
# self.audio['bps']) = [int(x) for x in audio_props[1:]]
#
# if self.audio['streams'] > 0:
# self.current_audio_stream = 1
# self.current_volume = 0.0

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
        """
Returns the number of 600s, and 30s seeks to get to the time nearest to target_offset.
"""

        # Need to determine the nearest time to target_offset, one of:
        #
        # curr_offset - 30*n (some multiple of the lowest granularity in the past)
        # curr_offset (simply don't seek)
        # curr_offset + 30*n (some multiple of the lowest granularity in the future)
        #
        # More precisely:
        #
        # n = argmin | curr_offset + i*30 - target_offset |
        # i
        #
        # For some i,
        #
        # curr_offset + i*30 <= target_offset <= curr_offset + (i+1)*30
        # i*30 <= target_offset - curr_offset <= (i+1)*30
        # i <= (offset - curr_offset) / 30 <= (i+1)
        # i = floor( (offset - curr_offset) / 30 )

        diff = target_offset - curr_offset
        large_seeks = int(math.floor(diff / 600.0))
        diff -= large_seeks*600
        small_seeks = int(math.floor(diff / 30.0))
        return large_seeks, small_seeks

    def seek_forward_30(self):
        """
Seeks forward by 30 seconds.
"""
        self._process.send(self._SEEK_FORWARD_30_CMD)

    def seek_forward_600(self):
        """
Seeks forward by 600 seconds.
"""
        self._process.send(self._SEEK_FORWARD_600_CMD)

    def seek_backward_30(self):
        """
Seeks backward by 30 seconds.
"""
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