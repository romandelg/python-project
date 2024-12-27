# Import necessary libraries
import mido  # Library for working with MIDI messages
import numpy as np  # Library for numerical operations
import sounddevice as sd  # Library for audio playback
import threading  # Library for threading
import time  # Library for time-related functions
import signal  # Library for handling signals
import sys  # Library for system-specific parameters and functions
from midi_handler import MIDIHandler  # Import MIDIHandler class
from synthesizer import Synthesizer  # Import Synthesizer class
from event_handler import EventHandler  # Import EventHandler class
from adsr import ADSR  # Import ADSR class
from oscillator import Oscillator  # Import Oscillator class
from gui_display import SynthesizerGUI  # Import SynthesizerGUI class
from terminal_display import TerminalDisplay  # Import TerminalDisplay class

def midi_handler_thread(midi_handler, port_name):
    midi_handler.start(port_name if port_name else None)

def main():
    synthesizer = Synthesizer()
    adsr = ADSR()
    event_handler = EventHandler(synthesizer, adsr)
    midi = MIDIHandler(event_handler)
    midi.scan_devices()
    
    port_name = input("Enter MIDI device name (or press Enter for first available): ").strip()
    
    # Start MIDI handling in a separate thread
    midi_thread = threading.Thread(target=midi_handler_thread, args=(midi, port_name), daemon=True)
    midi_thread.start()
    
    # Create and start GUI in the main thread
    gui = SynthesizerGUI()
    TerminalDisplay.set_gui(gui)  # Set GUI instance for terminal display
    
    # Add a cleanup handler
    def on_closing():
        print("\nShutting down...")
        midi.running = False
        gui.on_closing()
        sys.exit(0)
    
    gui.root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Start GUI mainloop in main thread
    try:
        gui.start()
    except KeyboardInterrupt:
        on_closing()

if __name__ == "__main__":
    main()