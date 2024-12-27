import numpy as np
import sounddevice as sd
import queue
import copy
import time
import threading

# Use relative imports
from .oscillator import Oscillator
from .filter import LowPassFilter
from .adsr import ADSR
from .terminal_display import print_all_values
from .audio_chain import AudioChainHandler, AudioModule
from .effects import Reverb, Distortion, Delay, Flanger, Chorus

class OscillatorModule(AudioModule):
    def __init__(self, oscillator):
        super().__init__("oscillator")
        self.oscillator = oscillator

    def _process_audio(self, signal):
        return signal

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
    """
    Main synthesizer class that manages voices, audio processing, and effects.
    Handles MIDI input, voice allocation, and audio output generation.
    """
    def __init__(self):
        # Audio settings
        self.sample_rate = 44100  # Standard audio sample rate
        self.buffer_size = 256    # Add this line to fix the error
        self.active_voices = {}   # Currently playing notes
        self.released_voices = {} # Notes in release phase
        self.event_queue = queue.Queue()  # Thread-safe event queue
        self.running = True       # Add this line for process_audio loop control
        
        # Initialize audio output stream
        self.stream = sd.OutputStream(
            channels=1,           # Mono output
            callback=self.audio_callback,
            samplerate=self.sample_rate,
            blocksize=self.buffer_size  # Use buffer_size here
        )
        
        # Core synthesizer components
        self.oscillator = Oscillator()     # Waveform generator
        self.filter = LowPassFilter()      # Main filter
        self.adsr = ADSR()                # Envelope generator
        
        # Audio processing chains
        self.audio_chain = AudioChainHandler()          # Main audio chain
        self.voice_chain_template = AudioChainHandler() # Template for new voices
        self.effects_chain = AudioChainHandler()        # Global effects chain
        
        # Set up audio chain modules
        self._initialize_audio_chains()
        
        # Performance and safety features
        self.voice_gain = 0.25           # Master volume control
        self.max_voices = 16             # Polyphony limit
        self.dc_block = DCBlocker()      # DC offset removal
        self.safety_limiter = SafetyLimiter()  # Prevent clipping
        
        # Thread synchronization
        self.param_lock = threading.Lock()  # Parameter changes lock
        self.voice_lock = threading.Lock()  # Voice management lock
        
        # Start audio processing
        self.stream.start()

    def _initialize_audio_chains(self):
        """Set up the audio processing chains with their modules"""
        # Main chain
        self.audio_chain.add_module(OscillatorModule(self.oscillator))
        self.audio_chain.add_module(FilterModule(self.filter))
        self.audio_chain.add_module(ADSRModule(self.adsr))
        
        # Voice template
        self.voice_chain_template.add_module(OscillatorModule(self.oscillator))
        self.voice_chain_template.add_module(FilterModule(self.filter))
        
        # Initialize and add effects
        self._initialize_effects()

    def _initialize_effects(self):
        """Initialize effect modules and add them to the effects chain"""
        self.effects = {
            'reverb': Reverb(),
            'distortion': Distortion(),
            'delay': Delay(),
            'flanger': Flanger(),
            'chorus': Chorus()
        }
        for effect in self.effects.values():
            self.effects_chain.add_effect(effect)

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
        """
        Real-time audio generation callback.
        Called by sounddevice for each audio buffer that needs to be filled.
        
        Args:
            outdata: Output buffer to fill with audio samples
            frames: Number of frames to generate
            time: Current stream time
            status: Stream status flags
        """
        try:
            outdata.fill(0)
            temp_buffer = np.zeros_like(outdata[:, 0], dtype=np.float64)
            
            with self.voice_lock:
                if self.active_voices or self.released_voices:
                    duration = frames / self.sample_rate
                    active_voice_count = len(self.active_voices) + len(self.released_voices)
                    voice_gain = self.voice_gain / max(1, np.sqrt(active_voice_count))
                    
                    self._process_active_voices(temp_buffer, duration, voice_gain)
                    self._process_released_voices(temp_buffer, duration, voice_gain)
                    
                    temp_buffer = self.dc_block.process(temp_buffer)
                    temp_buffer = self.safety_limiter.process(temp_buffer)
            
            if np.any(np.isnan(temp_buffer)) or np.any(np.isinf(temp_buffer)):
                temp_buffer.fill(0)
            
            np.clip(temp_buffer, -1.0, 1.0, out=outdata[:, 0])
            
        except Exception as e:
            print(f"Audio callback error: {e}")
            outdata.fill(0)

    def _process_active_voices(self, buffer, duration, gain):
        """
        Process all currently active (playing) voices.
        
        Args:
            buffer: Output buffer to accumulate voice samples
            duration: Length of audio to generate in seconds
            gain: Per-voice amplitude scaling factor
        """
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

    def process_audio(self):
        """Process audio in a thread-safe manner"""
        while self.running:
            try:
                mixed_output = np.zeros(self.buffer_size)
                
                with self.voice_lock:
                    # Process active voices
                    for voice in self.active_voices:
                        if voice.playing:
                            voice_output = np.zeros(self.buffer_size)
                            mixed_output += voice_output
                    
                    # Normalize if needed
                    if len(self.active_voices) > 0:
                        mixed_output /= len(self.active_voices)
                    
                    # Process through effects chain
                    if self.effects_chain:
                        mixed_output = self.effects_chain.process(mixed_output)
                
                # Yield the mixed output outside the lock
                yield mixed_output
                
            except Exception as e:
                print(f"Process audio error: {e}")
                yield np.zeros(self.buffer_size)

    def stop(self):
        """Safely stop audio processing"""
        self.running = False

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

"""
Synthesizer Core Architecture:
1. Voice Management
   - Polyphonic voice allocation
   - Note tracking and release handling
   - Voice limit management

2. Audio Processing Chain:
   Input → Oscillator → Filter → ADSR → Effects → Output

3. Parameter Management:
   - MIDI CC mapping
   - Real-time parameter updates
   - Voice parameter synchronization

4. Safety Features:
   - DC blocking
   - Safety limiting
   - Buffer overrun protection
   - Exception handling

Audio Callback Flow:
1. Process pending events (note on/off)
2. Generate voice waveforms
3. Apply voice-specific processing
4. Mix active voices
5. Process through effects
6. Apply safety checks
7. Output final audio

Threading Considerations:
- Uses locks for parameter changes
- Safe voice allocation/deallocation
- Thread-safe event queue
"""
