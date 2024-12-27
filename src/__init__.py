"""Event-Driven Synthesizer Package"""

# Core components
from .synthesizer import Synthesizer
from .oscillator import Oscillator
from .filter import LowPassFilter
from .adsr import ADSR

# Event handling
from .midi_handler import MIDIHandler
from .event_handler import EventHandler

# Display
from .terminal_display import TerminalDisplay
from .gui_display import SynthesizerGUI

# Audio processing
from .audio_chain import AudioChainHandler, AudioModule
from .effects import Reverb, Distortion, Delay, Flanger, Chorus

__all__ = [
    'Synthesizer',
    'MIDIHandler',
    'EventHandler',
    'Oscillator',
    'ADSR',
    'LowPassFilter',
    'TerminalDisplay',
    'SynthesizerGUI',
    'AudioChainHandler',
    'AudioModule',
    'Reverb',
    'Distortion',
    'Delay',
    'Flanger',
    'Chorus'
]