import numpy as np
import sounddevice as sd
import queue
from oscillator import Oscillator
from filter import LowPassFilter  # Import LowPassFilter
from adsr import ADSR  # Add ADSR import
from terminal_display import print_all_values  # Import the new function

class Synthesizer:
    def __init__(self):
        self.sample_rate = 44100
        self.active_voices = {}
        self.event_queue = queue.Queue()
        self.stream = sd.OutputStream(
            channels=1,
            callback=self.audio_callback,
            samplerate=self.sample_rate,
            blocksize=256
        )
        self.stream.start()
        self.oscillator = Oscillator()
        self.filter = LowPassFilter()  # Add filter instance
        self.adsr = ADSR()  # Initialize ADSR instance

    def note_on(self, note, velocity):
        freq = 440.0 * (2.0 ** ((note - 69) / 12.0))
        self.event_queue.put(('note_on', note, velocity, freq))

    def note_off(self, note):
        self.event_queue.put(('note_off', note))

    def control_change(self, control, value):
        cc_to_osc = {
            14: 'sine',
            15: 'saw',
            16: 'triangle',
            17: 'pulse'
        }
        if control in cc_to_osc:
            print(f"\nReceived CC{control} [{cc_to_osc[control]}]: {value}/127 = {value/127:.2f}")
            self.oscillator.set_mix_level(cc_to_osc[control], value)
        elif control == 22:
            self.filter.set_cutoff_freq(value * 100.0)  # Scale to 0-12700 Hz
        elif control == 23:
            self.filter.set_resonance(value / 127.0)
        elif control in [18, 19, 20, 21]:
            self.adsr_control_change(control, value)

        # Print all values
        print_all_values(
            self.oscillator.mix_levels,
            self.filter.cutoff_freq,
            self.filter.resonance,
            self.adsr.attack,
            self.adsr.decay,
            self.adsr.sustain,
            self.adsr.release
        )

    def adsr_control_change(self, control, value):
        if control == 18:
            self.adsr.set_attack(value / 127.0)
        elif control == 19:
            self.adsr.set_sustain(value / 127.0)
        elif control == 20:
            self.adsr.set_decay(value / 127.0)
        elif control == 21:
            self.adsr.set_release(value / 127.0)

    def audio_callback(self, outdata, frames, time, status):
        outdata.fill(0)
        
        # Process events
        while not self.event_queue.empty():
            event = self.event_queue.get()
            if event[0] == 'note_on':
                _, note, _, freq = event  # Ignore velocity
                if note not in self.active_voices:
                    self.active_voices[note] = Voice(freq)
                    self.active_voices[note].playing = True
            elif event[0] == 'note_off' and event[1] in self.active_voices:
                del self.active_voices[event[1]]

        # Generate audio with fixed amplitude
        if self.active_voices:
            for voice in list(self.active_voices.values()):
                duration = frames / self.sample_rate
                waveform = self.oscillator.generate(voice.freq, self.sample_rate, duration)
                outdata[:, 0] += 0.5 * waveform  # Fixed amplitude of 0.5
                voice.phase = (voice.phase + frames) % self.sample_rate
            
            # Apply low pass filter
            outdata[:, 0] = self.filter.apply_filter(outdata[:, 0])
            
            # Soft clip the final output
            outdata[:, 0] = np.tanh(outdata[:, 0])

class Voice:
    def __init__(self, freq):  # Remove velocity parameter
        self.freq = freq
        self.playing = False
        self.phase = 0.0
