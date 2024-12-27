"""Main Entry Point and Program Flow"""

# Ensure all required packages are installed
try:
    import mido
    import numpy as np
    import sounddevice as sd
except ImportError as e:
    print(f"Missing required package: {e}")
    print("Please install required packages using:")
    print("pip install mido numpy sounddevice")
    exit(1)

# Standard library imports
import threading
import time
import signal
import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

# Local imports using relative imports
from .synthesizer import Synthesizer
from .midi_handler import MIDIHandler
from .event_handler import EventHandler
from .adsr import ADSR
from .oscillator import Oscillator
from .gui_display import SynthesizerGUI
from .terminal_display import TerminalDisplay, start_gui

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