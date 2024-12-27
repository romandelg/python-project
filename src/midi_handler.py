import mido
import time
import signal
import sys
from event_handler import EventHandler
from adsr import ADSR
from filter import LowPassFilter

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
            print("\nStopping...")

    def handle_control_change(self, message):
        if message.control == 18:
            self.adsr.set_attack(message.value / 127.0)
        elif message.control == 19:
            self.adsr.set_sustain(message.value / 127.0)
        elif message.control == 20:
            self.adsr.set_decay(message.value / 127.0)
        elif message.control == 21:
            self.adsr.set_release(message.value / 127.0)
        elif message.control == 22:
            self.filter.set_cutoff_freq(message.value * 100.0)  # Scale to 0-12700 Hz
        elif message.control == 23:
            self.filter.set_resonance(message.value / 127.0)
