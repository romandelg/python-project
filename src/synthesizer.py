import numpy as np
import sounddevice as sd
import queue
from oscillator import Oscillator
from filter import LowPassFilter
from adsr import ADSR
from terminal_display import print_all_values
from audio_chain import AudioChainHandler, AudioModule

class OscillatorModule(AudioModule):
    def __init__(self, oscillator):
        super().__init__("oscillator")
        self.oscillator = oscillator

    def _process_audio(self, signal):
        return signal  # The oscillator generates rather than processes

class FilterModule(AudioModule):
    def __init__(self, filter):
        super().__init__("filter")
        self.filter = filter

    def _process_audio(self, signal):
        return self.filter.apply_filter(signal)

class ADSRModule(AudioModule):
    def __init__(self, adsr):
        super().__init__("adsr")
        self.adsr = adsr

    def _process_audio(self, signal):
        return self.adsr.apply_envelope(signal)

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
        
        # Initialize components
        self.oscillator = Oscillator()
        self.filter = LowPassFilter()
        self.adsr = ADSR()
        
        # Setup audio chain
        self.audio_chain = AudioChainHandler()
        self.audio_chain.add_module(OscillatorModule(self.oscillator))
        self.audio_chain.add_module(FilterModule(self.filter))
        self.audio_chain.add_module(ADSRModule(self.adsr))
        
        self.stream.start()

    def note_on(self, note):
        freq = 440.0 * (2.0 ** ((note - 69) / 12.0))
        self.event_queue.put(('note_on', note, freq))

    def note_off(self, note):
        self.event_queue.put(('note_off', note))

    def control_change(self, control, value):
        cc_to_osc = {
            14: ('sine', 'mix'), 15: ('saw', 'mix'), 16: ('triangle', 'mix'), 17: ('pulse', 'mix'),
            26: ('sine', 'detune'), 27: ('saw', 'detune'), 28: ('triangle', 'detune'), 29: ('pulse', 'detune')
        }
        if control in cc_to_osc:
            osc_type, param_type = cc_to_osc[control]
            if param_type == 'mix':
                self.oscillator.set_mix_level(osc_type, value)
            else:
                self.oscillator.set_detune(osc_type, value)
        elif control == 22:
            self.filter.set_cutoff_freq(value * 100.0)
        elif control == 23:
            self.filter.set_resonance(value / 127.0)
        elif control in [18, 19, 20, 21]:
            self.adsr_control_change(control, value)

        print_all_values(
            self.oscillator.mix_levels,
            self.oscillator.detune_values,
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
        while not self.event_queue.empty():
            event = self.event_queue.get()
            if event[0] == 'note_on':
                _, note, freq = event
                if note not in self.active_voices:
                    self.active_voices[note] = Voice(freq)
            elif event[0] == 'note_off' and event[1] in self.active_voices:
                del self.active_voices[event[1]]

        if self.active_voices:
            for voice in self.active_voices.values():
                duration = frames / self.sample_rate
                waveform = self.oscillator.generate(voice.freq, self.sample_rate, duration)
                outdata[:, 0] += 0.5 * waveform
                voice.phase = (voice.phase + frames) % self.sample_rate
            
            # Process through audio chain
            outdata[:, 0] = self.audio_chain.process_audio(outdata[:, 0])
            outdata[:, 0] = np.tanh(outdata[:, 0])  # Soft clipping

class Voice:
    def __init__(self, freq):
        self.freq = freq
        self.phase = 0.0
