import numpy as np
import sounddevice as sd
import queue
import copy
import time
import threading
from oscillator import Oscillator
from filter import LowPassFilter
from adsr import ADSR
from terminal_display import print_all_values
from audio_chain import AudioChainHandler, AudioModule
from effects import Reverb, Distortion, Delay, Flanger, Chorus

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
        self.released_voices = {}  # Store voices that are in release phase
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
        
        # Create template audio chain for voices
        self.voice_chain_template = AudioChainHandler()
        self.voice_chain_template.add_module(OscillatorModule(self.oscillator))
        self.voice_chain_template.add_module(FilterModule(self.filter))
        
        # Global effects chain
        self.effects_chain = AudioChainHandler()
        
        # Initialize modulation sources
        self.mod_sources = {
            'lfo1': 0.0,
            'lfo2': 0.0,
            'env1': 0.0,
            'env2': 0.0,
        }
        
        # Initialize effects
        self.effects = {
            'reverb': Reverb(),
            'distortion': Distortion(),
            'delay': Delay(),
            'flanger': Flanger(),
            'chorus': Chorus()
        }
        
        # Add effects to chain
        for effect in self.effects.values():
            self.effects_chain.add_effect(effect)
        
        self.param_lock = threading.Lock()
        self.voice_lock = threading.Lock()
        
        self.stream.start()
        self.voice_gain = 0.25  # Reduced default gain
        self.max_voices = 16    # Limit maximum concurrent voices
        self.dc_block = DCBlocker()  # Add DC blocking
        self.safety_limiter = SafetyLimiter()  # Add safety limiter

    def note_on(self, note):
        with self.voice_lock:
            # Limit maximum voices
            if len(self.active_voices) >= self.max_voices:
                oldest_note = min(self.active_voices.keys(), 
                                key=lambda k: self.active_voices[k].note_on_time)
                self.note_off(oldest_note)
            
            try:
                freq = 440.0 * (2.0 ** ((note - 69) / 12.0))
                voice = Voice(freq, self.voice_chain_template)
                voice.adsr.note_on()
                self.active_voices[note] = voice
                self.event_queue.put(('note_on', note, freq))
            except Exception as e:
                print(f"Note on error: {e}")

    def note_off(self, note):
        if note in self.active_voices:
            voice = self.active_voices.pop(note)
            voice.release_triggered = True
            voice.adsr.note_off()  # Trigger release phase
            self.released_voices[note] = voice
        self.event_queue.put(('note_off', note))

    def control_change(self, control, value):
        with self.param_lock:
            try:
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
                elif control == 22:  # Filter cutoff
                    cutoff = 20.0 * np.exp(np.log(1000) * value / 127.0)
                    self.filter.set_cutoff_freq(cutoff)
                    # Update all voice filters
                    for voice in self.active_voices.values():
                        voice.filter.set_cutoff_freq(cutoff)
                    for voice in self.released_voices.values():
                        voice.filter.set_cutoff_freq(cutoff)
                elif control == 23:  # Filter resonance
                    resonance = 0.1 + (9.9 * value / 127.0)
                    self.filter.set_resonance(resonance)
                    # Update all voice filters
                    for voice in self.active_voices.values():
                        voice.filter.set_resonance(resonance)
                    for voice in self.released_voices.values():
                        voice.filter.set_resonance(resonance)
                elif control in [18, 19, 20, 21]:
                    self.adsr_control_change(control, value)

                # Effects controls (CC 102-106)
                effect_ccs = {
                    102: 'reverb', 103: 'distortion', 104: 'delay',
                    105: 'flanger', 106: 'chorus'
                }
                
                if control in effect_ccs:
                    effect_name = effect_ccs[control]
                    if effect_name in self.effects:
                        effect = self.effects[effect_name]
                        dry_wet = value / 127.0
                        effect.wet = dry_wet
                        effect.dry = 1.0 - dry_wet
                        print_effect_values(effect_name, effect.enabled, dry_wet)

            except Exception as e:
                print(f"Control change error: {e}")

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
        try:
            outdata.fill(0)
            temp_buffer = np.zeros_like(outdata[:, 0], dtype=np.float64)  # Use double precision
            
            # Process events with lock
            while not self.event_queue.empty():
                event = self.event_queue.get()
                with self.voice_lock:
                    if event[0] == 'note_on':
                        _, note, freq = event
                        if note in self.active_voices:
                            self.active_voices[note].adsr.note_on()
                    elif event[0] == 'note_off':
                        _, note = event

            # Process voices with lock
            with self.voice_lock:
                if self.active_voices or self.released_voices:
                    try:
                        duration = frames / self.sample_rate
                        active_voice_count = len(self.active_voices) + len(self.released_voices)
                        voice_gain = self.voice_gain / max(1, np.sqrt(active_voice_count))

                        self._process_active_voices(temp_buffer, duration, voice_gain)
                        self._process_released_voices(temp_buffer, duration, voice_gain)
                        
                        # Apply DC blocking and limiting
                        temp_buffer = self.dc_block.process(temp_buffer)
                        temp_buffer = self.safety_limiter.process(temp_buffer)
                    except Exception as e:
                        print(f"Voice processing error: {e}")
                        temp_buffer.fill(0)

            # Final safety check
            if np.any(np.isnan(temp_buffer)) or np.any(np.isinf(temp_buffer)):
                temp_buffer.fill(0)
            
            np.clip(temp_buffer, -1.0, 1.0, out=outdata[:, 0])

        except Exception as e:
            print(f"Audio callback error: {e}")
            outdata.fill(0)

    def _process_active_voices(self, buffer, duration, gain):
        for voice in list(self.active_voices.values()):
            try:
                waveform = self.oscillator.generate(voice.freq, self.sample_rate, duration)
                processed = voice.audio_chain.process_voice(voice, waveform)
                processed = voice.adsr.apply_envelope(processed)
                np.add(buffer, np.clip(processed * gain, -1.0, 1.0), out=buffer)
            except Exception as e:
                print(f"Active voice processing error: {e}")

    def _process_released_voices(self, buffer, duration, gain):
        released_done = []
        for note, voice in self.released_voices.items():
            try:
                if voice.is_finished():
                    released_done.append(note)
                    continue
                
                waveform = self.oscillator.generate(voice.freq, self.sample_rate, duration)
                processed = voice.audio_chain.process_voice(voice, waveform)
                processed = voice.adsr.apply_envelope(processed)
                np.add(buffer, np.clip(processed * gain, -1.0, 1.0), out=buffer)
            except Exception as e:
                print(f"Released voice processing error: {e}")
                released_done.append(note)
        
        for note in released_done:
            self.released_voices.pop(note, None)

    def toggle_effect(self, effect_name, enabled):
        if effect_name in self.effects:
            self.effects[effect_name].enabled = enabled
            print_effect_values(effect_name, enabled, self.effects[effect_name].wet)

class Voice:
    def __init__(self, freq, template_chain=None):
        self.freq = freq
        self.phase = 0.0
        self.active = True
        self.release_triggered = False
        self.adsr = ADSR()
        self.filter = LowPassFilter()  # Each voice gets its own filter instance
        self.audio_chain = self._create_chain(template_chain)
        self.note_on_time = time.time()

    def _create_chain(self, template):
        """Create a new chain based on template without copying locks"""
        if template is None:
            return None
        
        chain = AudioChainHandler()
        # Copy modules with their own filter instances
        for module in template.chain:
            if isinstance(module, OscillatorModule):
                chain.add_module(OscillatorModule(module.oscillator))
            elif isinstance(module, FilterModule):
                chain.add_module(FilterModule(self.filter))  # Use voice's filter
            elif isinstance(module, ADSRModule):
                chain.add_module(ADSRModule(self.adsr))
        return chain

    def is_finished(self):
        return self.release_triggered and self.adsr.current_state == 'off'

class DCBlocker:
    def __init__(self):
        self.x1 = 0.0
        self.y1 = 0.0
        self.R = 0.995

    def process(self, signal):
        output = np.zeros_like(signal)
        for i in range(len(signal)):
            output[i] = signal[i] - self.x1 + self.R * self.y1
            self.x1 = signal[i]
            self.y1 = output[i]
        return output

class SafetyLimiter:
    def __init__(self, threshold=0.95, release_time=0.1):
        self.threshold = threshold
        self.release_coeff = np.exp(-1.0 / (44100 * release_time))
        self.envelope = 0.0

    def process(self, signal):
        output = signal.copy()
        for i in range(len(signal)):
            abs_sample = abs(signal[i])
            if abs_sample > self.envelope:
                self.envelope = abs_sample
            else:
                self.envelope *= self.release_coeff

            if self.envelope > self.threshold:
                gain_reduction = self.threshold / self.envelope
                output[i] *= gain_reduction

        return output
