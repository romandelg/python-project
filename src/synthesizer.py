import numpy as np
import sounddevice as sd
import queue
from oscillator import Oscillator
from filter import LowPassFilter  # Import LowPassFilter

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

    def audio_callback(self, outdata, frames, time, status):
        outdata.fill(0)
        
        # Process events
        while not self.event_queue.empty():
            event = self.event_queue.get()
            if event[0] == 'note_on':
                _, note, velocity, freq = event
                if note not in self.active_voices:
                    self.active_voices[note] = Voice(freq, velocity)
                    self.active_voices[note].playing = True
            elif event[0] == 'note_off' and event[1] in self.active_voices:
                del self.active_voices[event[1]]

        # Generate audio with proper scaling
        if self.active_voices:
            for voice in list(self.active_voices.values()):
                duration = frames / self.sample_rate
                waveform = self.oscillator.generate(voice.freq, self.sample_rate, duration)
                outdata[:, 0] += 0.5 * (voice.velocity / 127.0) * waveform
                voice.phase = (voice.phase + frames) % self.sample_rate
            
            # Apply low pass filter
            outdata[:, 0] = self.filter.apply_filter(outdata[:, 0])
            
            # Soft clip the final output
            outdata[:, 0] = np.tanh(outdata[:, 0])

class Voice:
    def __init__(self, freq, velocity):
        self.freq = freq
        self.velocity = velocity
        self.playing = False
        self.phase = 0.0
