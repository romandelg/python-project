import mido
import time
import signal
import sys
from event_handler import EventHandler
from adsr import ADSR
from filter import LowPassFilter

"""
MIDI Input Processing:
1. Scans and connects to MIDI devices
2. Receives MIDI messages in real-time
3. Converts MIDI messages to synth events
4. Routes control changes to appropriate parameters

Message Types Handled:
- Note On (key press)
- Note Off (key release)
- Control Change (knob/slider movements)
  * CC 14-17: Oscillator mix levels
  * CC 26-29: Oscillator detune
  * CC 18-21: ADSR parameters
  * CC 22-23: Filter parameters
  * CC 102-106: Effect controls
"""

class MIDIHandler:    
    def __init__(self, event_handler):
        self.event_handler = event_handler
        self.running = True
        self.adsr = ADSR()
        self.filter = LowPassFilter()
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        print("\nShutting down...")
        self.running = False
        sys.exit(0)
        
    def scan_devices(self):
        print("Available MIDI input ports:")
        for port in mido.get_input_names():
            print(f"- {port}")
            
    def start(self, port_name=None):
        if not port_name:
            ports = mido.get_input_names()
            if not ports:
                print("No MIDI devices found!")
                return
            port_name = ports[0]
            
        try:
            with mido.open_input(port_name) as midi_port:
                print(f"Listening on {port_name}")
                print("Press Ctrl+C to stop...")
                while self.running:
                    for message in midi_port.iter_pending():
                        if message.type in ['note_on', 'note_off', 'control_change']:
                            self.event_handler.handle_event(message)
                        if message.type == 'control_change':
                            self.handle_control_change(message)
                    time.sleep(0.001)
        except KeyboardInterrupt:
            self.running = False
            print("\nStopping...")
        except Exception as e:
            print(f"MIDI Error: {e}")
            self.running = False

    def handle_control_change(self, message):
        self.event_handler.handle_control_change(message.control, message.value)
