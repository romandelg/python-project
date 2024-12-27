import mido  # Library for working with MIDI messages
import time  # Library for time-related functions
import signal  # Library for handling signals
import sys  # Library for system-specific parameters and functions
from event_handler import EventHandler  # Import EventHandler class

class MIDIHandler:
    # Array of note names for converting MIDI numbers to musical notation
    NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    
    def __init__(self, event_handler):
        # Initialize event handler instance
        self.event_handler = event_handler
        # Flag to keep the program running
        self.running = True
        # Set up signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
    
    # Signal handler for graceful shutdown
    def _signal_handler(self, signum, frame):
        print("\nShutting down...")
        self.running = False
        sys.exit(0)
    
    # Convert MIDI note number to musical notation (e.g., C4, A#3)
    def get_note_name(self, midi_note):
        octave = (midi_note // 12) - 1
        note = self.NOTE_NAMES[midi_note % 12]
        return f"{note}{octave}"
        
    # List all available MIDI input devices
    def scan_devices(self):
        print("Available MIDI input ports:")
        for port in mido.get_input_names():
            print(f"- {port}")
            
    # Start listening to MIDI input from the specified port
    def start(self, port_name=None):
        if not port_name:
            # If no port name is provided, use the first available port
            available_ports = mido.get_input_names()
            if not available_ports:
                print("No MIDI devices found!")
                return
            port_name = available_ports[0]
            
        try:
            # Open the specified MIDI input port
            with mido.open_input(port_name) as midi_port:
                print(f"Listening on {port_name}")
                print("Press Ctrl+C to stop...")
                while self.running:
                    # Process all pending MIDI messages
                    for message in midi_port.iter_pending():
                        self._handle_message(message)
                    time.sleep(0.001)
        except KeyboardInterrupt:
            print("\nStopping...")
    
    # Process incoming MIDI messages
    def _handle_message(self, message):
        if message.type == 'note_on' or message.type == 'note_off':
            self.event_handler.handle_event(message)
