import snowboydecoder
import sys
import signal
#import RPi.GPIO as GPIO
import time
import imp
import logging
import os
import subprocess
import google.auth.transport.grpc
import google.auth.transport.requests
import google.oauth2.credentials
import json
from actions import load_settings
from actions import misc

from google.assistant.embedded.v1alpha2 import (
    embedded_assistant_pb2,
    embedded_assistant_pb2_grpc
)
from tenacity import retry, stop_after_attempt, retry_if_exception

try:
    from googlesamples.assistant.grpc import (
        assistant_helpers,
        audio_helpers,
        device_helpers
    )
except SystemError:
    import assistant_helpers
    import audio_helpers
    import device_helpers

from pushbutton import SampleAssistant
#subprocess.Popen(["aplay", "/home/pi/GassistPi/sample-audio-files/customwakeword.wav"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
ROOT_PATH = os.path.realpath(os.path.join(__file__, '..', '..'))
resources = {'fb':'{}/sample-audio-files/Fb.wav'.format(ROOT_PATH),'startup':'{}/sample-audio-files/Startup.wav'.format(ROOT_PATH)}

misc.play_audio_file(resources['startup'])
# GPIO.setmode(GPIO.BCM)
# GPIO.setwarnings(False)
# interrupted = False
# GPIO.setup(22,GPIO.OUT)
# GPIO.output(22,GPIO.LOW)

logging.basicConfig(filename='/tmp/GassistPi_snowboy.log', level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger=logging.getLogger(__name__)

INFO_FILE = os.path.expanduser('~/gassistant-credentials.info')

settings = load_settings()

#Add your custom models here
models = ['{}/src/resources/models/smart_mirror.umdl'.format(ROOT_PATH), '{}/src/resources/models/snowboy.umdl'.format(ROOT_PATH)]
interrupted=False
def signal_handler(signal, frame):
    global interrupted
    interrupted = True



def interrupt_callback():
    global interrupted
    return interrupted

def main():
  args = imp.load_source('args',INFO_FILE)
  if not hasattr(args,'credentials'):
      args.credentials = os.path.join(os.path.expanduser('~/.config'),'google-oauthlib-tool','credentials.json')
  if not hasattr(args,'device_config'):
      args.device_config=os.path.join(os.path.expanduser('~/.config'),'googlesamples-assistant','device_config.json')
  verbose=False
  credentials=args.credentials
  project_id=args.project_id
  device_config = args.device_config
  device_id=''
  device_model_id=args.device_model_id
  api_endpoint='embeddedassistant.googleapis.com'
  audio_sample_rate=audio_helpers.DEFAULT_AUDIO_SAMPLE_RATE
  audio_sample_width=audio_helpers.DEFAULT_AUDIO_SAMPLE_WIDTH
  audio_block_size=audio_helpers.DEFAULT_AUDIO_DEVICE_BLOCK_SIZE
  audio_flush_size=audio_helpers.DEFAULT_AUDIO_DEVICE_FLUSH_SIZE
  audio_iter_size=audio_helpers.DEFAULT_AUDIO_ITER_SIZE
  grpc_deadline=60 * 3 + 5
  lang='en-US'
  once=False
  try:
      with open(credentials, 'r') as f:
          credentials = google.oauth2.credentials.Credentials(token=None,
                                                              **json.load(f))
          http_request = google.auth.transport.requests.Request()
          credentials.refresh(http_request)
  except Exception as e:
      logging.error('Error loading credentials: %s', e)
      logging.error('Run google-oauthlib-tool to initialize '
                    'new OAuth 2.0 credentials.')
      sys.exit(-1)
  grpc_channel = google.auth.transport.grpc.secure_authorized_channel(
      credentials, http_request, api_endpoint)
  logging.info('Connecting to %s', api_endpoint)

  # Configure audio source and sink.
  audio_device = None
  audio_source = audio_device = (
    audio_device or  audio_helpers.SoundDeviceStream(
          sample_rate=audio_sample_rate,
          sample_width=audio_sample_width,
          block_size=audio_block_size,
          flush_size=audio_flush_size
          )
      
  )

  audio_sink = audio_device = (
    audio_device or audio_helpers.SoundDeviceStream(
          sample_rate=audio_sample_rate,
          sample_width=audio_sample_width,
          block_size=audio_block_size,
          flush_size=audio_flush_size
          )
      
  )
  # Create conversation stream with the given audio source and sink.
  conversation_stream = audio_helpers.ConversationStream(
      source=audio_source,
      sink=audio_sink,
      iter_size=audio_iter_size,
      sample_width=audio_sample_width,
  )
  if not device_id or not device_model_id:
      try:
          with open(device_config) as f:
              device = json.load(f)
              device_id = device['id']
              device_model_id = device['model_id']
              logging.info("Using device model %s and device id %s",
                           device_model_id,
                           device_id)
      except Exception as e:
          logging.warning('Device config not found: %s' % e)
          logging.info('Registering device')
          if not device_model_id:
              logging.error('Option --device-model-id required '
                            'when registering a device instance.')
              sys.exit(-1)
          if not project_id:
              logging.error('Option --project-id required '
                            'when registering a device instance.')
              sys.exit(-1)
          device_base_url = (
              'https://%s/v1alpha2/projects/%s/devices' % (api_endpoint,
                                                           project_id)
          )
          device_id = str(uuid.uuid1())
          payload = {
              'id': device_id,
              'model_id': device_model_id,
              'client_type': 'SDK_SERVICE'
          }
          session = google.auth.transport.requests.AuthorizedSession(
              credentials
          )
          r = session.post(device_base_url, data=json.dumps(payload))
          if r.status_code != 200:
              logging.error('Failed to register device: %s', r.text)
              sys.exit(-1)
          logging.info('Device registered: %s', device_id)
          pathlib.Path(os.path.dirname(device_config)).mkdir(exist_ok=True)
          with open(device_config, 'w') as f:
              json.dump(payload, f)
  device_handler = device_helpers.DeviceRequestHandler(device_id)

  @device_handler.command('action.devices.commands.OnOff')
  def onoff(on):
      if on:
          logging.info('Turning device on')
      else:
          logging.info('Turning device off')

  gassist = SampleAssistant(lang, device_model_id, device_id,
                           conversation_stream,
                           grpc_channel, grpc_deadline,device_handler)

  ###################### start snowboy code ###################
  def detected():
      # GPIO.output(22,GPIO.HIGH)
      # time.sleep(.05)
      # GPIO.output(22,GPIO.LOW)
      #snowboydecoder.play_audio_file(snowboydecoder.DETECT_DING)
      gassist.assist()


  # capture SIGINT signal, e.g., Ctrl+C
  signal.signal(signal.SIGINT, signal_handler)

  sensitivity = [0.5]*len(models)
  callbacks = [detected]*len(models)
  detector = snowboydecoder.HotwordDetector(models, sensitivity=sensitivity)

  # main loop
  # make sure you have the same numbers of callbacks and models
  detector.start(detected_callback=callbacks,
                 interrupt_check=interrupt_callback,
                 sleep_time=0.03)

  detector.terminate()


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        logger.exception(error)
