from googletrans import Translator
from gtts import gTTS
import vlc
try:
    import RPi.GPIO as GPIO
except Exception as e:
    if str(e) == 'No module named \'RPi\'':
        GPIO = None

## Other language options:
##'af'    : 'Afrikaans'         'sq' : 'Albanian'           'ar' : 'Arabic'      'hy'    : 'Armenian'
##'bn'    : 'Bengali'           'ca' : 'Catalan'            'zh' : 'Chinese'     'zh-cn' : 'Chinese (China)'
##'zh-tw' : 'Chinese (Taiwan)'  'hr' : 'Croatian'           'cs' : 'Czech'       'da'    : 'Danish'
##'nl'    : 'Dutch'             'en' : 'English'            'eo' : 'Esperanto'   'fi'    : 'Finnish'
##'fr'    : 'French'            'de' : 'German'             'el' : 'Greek'       'hi'    : 'Hindi'
##'hu'    : 'Hungarian'         'is' : 'Icelandic'          'id' : 'Indonesian'  'it'    : 'Italian'
##'ja'    : 'Japanese'          'km' : 'Khmer (Cambodian)'  'ko' : 'Korean'      'la'    : 'Latin'
##'lv'    : 'Latvian'           'mk' : 'Macedonian'         'no' : 'Norwegian'   'pl'    : 'Polish'
##'pt'    : 'Portuguese'        'ro' : 'Romanian'           'ru' : 'Russian'     'sr'    : 'Serbian'
##'si'    : 'Sinhala'           'sk' : 'Slovak'             'es' : 'Spanish'     'sw'    : 'Swahili'
##'sv'    : 'Swedish'           'ta' : 'Tamil'              'th' : 'Thai'        'tr'    : 'Turkish'
##'uk'    : 'Ukrainian'         'vi' : 'Vietnamese'         'cy' : 'Welsh'


class misc():

    def __init__(self):
        self.libvlc_Instance=vlc.Instance('--verbose 0')
        self.libvlc_player = self.libvlc_Instance.media_player_new()
        self.libvlc_list_player = self.libvlc_Instance.media_list_player_new()
        self.libvlc_Media_list = self.libvlc_Instance.media_list_new()
        self.libvlc_list_player.set_media_player(self.libvlc_player)
        self.libvlc_list_player.set_media_list(self.libvlc_Media_list)
        self.ttsfilename="/tmp/say.mp3"
        self.translator = Translator()
        self.language='en'


    def setup_GPIO(self):
        if GPIO != None:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)

            # Indicator Pins
            GPIO.setup(25, GPIO.OUT)
            GPIO.setup(5, GPIO.OUT)
            GPIO.setup(6, GPIO.OUT)
            GPIO.output(5, GPIO.LOW)
            GPIO.output(6, GPIO.LOW)
            self.led = GPIO.PWM(25, 1)
            self.led.start(0)                                       

    def set_GPIO(self,GPIO5=None,GPIO6=None,duty=None):
        #GPIO.HIGH is 1
        #GPIO.LOW is 0
        if GPIO != None:
            if GPIO5 !=None:
                GPIO.output(5, GPIO5)
            if GPIO6 !=None:
                GPIO.output(6, GPIO6)
            if duty != None:
                led.ChangeDutyCycle(duty)

    
    def play_audio_file(self,fname):
        Instance=vlc.Instance()
        player=Instance.media_player_new()
        player.set_mrl(fname)
        player.play()


    def vlc_play_item(self,mrl):
        media=self.libvlc_Instance.media_new(mrl)
        self.libvlc_Media_list.add_media(media)
        self.libvlc_list_player.play_item(media)

    def set_vlc_volume(self,level):
        self.libvlc_player.audio_set_volume(level)

    def get_vlc_volume(self):
        return self.libvlc_player.audio_get_volume()

    def mute_vlc(self,status=True):
        return self.libvlc_player.audio_set_mute(status)

    def stop_vlc(self):
        print('stopping vlc')
        self.libvlc_player.stop()

    def pause_vlc(self):
        print('pausing vlc')
        self.libvlc_player.pause()

    def play_vlc(self):
        print('playing/resuming vlc')
        self.libvlc_player.play()

    def is_vlc_playing(self):
        return self.libvlc_player.is_playing()

    #Text to speech converter with translation
    
    def say(self,words):
        try:
            os.remove(self.ttsfilename)
        except:
            pass
        words= self.translator.translate(words, dest=self.language)
        words=words.text
        words=words.replace("Text, ",'',1)
        words=words.strip()
        #print(words)
        tts = gTTS(text=words, lang=self.language)
        tts.save(self.ttsfilename)
        Instance=vlc.Instance()
        player=Instance.media_player_new()
        player.set_mrl(self.ttsfilename)
        player.play()