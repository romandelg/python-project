import numpy as np
from audio_chain import Effect
from terminal_display import print_effect_values

class Reverb(Effect):
    def __init__(self):
        super().__init__("reverb")
        self.room_size = 0.5
        self.damping = 0.5
        self.decay = 0.5
        self._delay_lines = []
        self._initialize_delays()

    def _initialize_delays(self):
        delay_times = [1553, 1559, 1567, 1571, 1579, 1583, 1597, 1601]  # Prime numbers
        self._delay_lines = [np.zeros(int(t)) for t in delay_times]
        self._delay_indexes = [0] * len(self._delay_lines)

    def _process_effect(self, signal):
        output = np.zeros_like(signal)
        for i, delay_line in enumerate(self._delay_lines):
            delay_output = delay_line[self._delay_indexes[i]]
            output += delay_output * (0.8 ** i)
            
            # Update delay line
            delay_line[self._delay_indexes[i]] = signal[0] + delay_output * self.decay
            self._delay_indexes[i] = (self._delay_indexes[i] + 1) % len(delay_line)
            
        return output * self.damping

class Distortion(Effect):
    def __init__(self):
        super().__init__("distortion")
        self.drive = 2.0
        self.tone = 0.5

    def _process_effect(self, signal):
        # Waveshaping distortion
        driven = np.tanh(signal * self.drive)
        # Simple tone control (low-pass filter)
        tone_filtered = np.convolve(driven, [self.tone, 1 - self.tone], mode='same')
        return tone_filtered

class Delay(Effect):
    def __init__(self):
        super().__init__("delay")
        self.delay_time = 0.3  # seconds
        self.feedback = 0.4
        self.sample_rate = 44100
        self._buffer_size = int(2 * self.sample_rate)  # 2 seconds max delay
        self._buffer = np.zeros(self._buffer_size)
        self._write_pos = 0
        self._delay_samples = int(self.delay_time * self.sample_rate)

    def _process_effect(self, signal):
        output = np.zeros_like(signal)
        for i in range(len(signal)):
            read_pos = (self._write_pos - self._delay_samples) % self._buffer_size
            output[i] = signal[i] + self._buffer[read_pos] * self.feedback
            self._buffer[self._write_pos] = signal[i]
            self._write_pos = (self._write_pos + 1) % self._buffer_size
        return output

class Flanger(Effect):
    def __init__(self):
        super().__init__("flanger")
        self.rate = 0.2  # Hz
        self.depth = 0.7
        self.feedback = 0.5
        self.phase = 0.0
        self._buffer = np.zeros(4410)  # 100ms buffer
        self._pos = 0

    def _process_effect(self, signal):
        output = np.zeros_like(signal)
        for i in range(len(signal)):
            # Calculate modulated delay
            mod_delay = int(self.depth * (np.sin(2 * np.pi * self.rate * self.phase) + 1) * 100)
            read_pos = (self._pos - mod_delay) % len(self._buffer)
            
            # Process sample
            output[i] = signal[i] + self._buffer[read_pos] * self.feedback
            self._buffer[self._pos] = signal[i]
            
            # Update positions
            self._pos = (self._pos + 1) % len(self._buffer)
            self.phase += 1.0 / 44100
        return output

class Chorus(Effect):
    def __init__(self):
        super().__init__("chorus")
        self.voices = 3
        self.rates = [0.5, 0.7, 0.9]  # Different rates for each voice
        self.depths = [0.6, 0.8, 0.7]  # Different depths for each voice
        self.phases = np.zeros(3)
        self._buffers = [np.zeros(4410) for _ in range(self.voices)]
        self._positions = [0] * self.voices

    def _process_effect(self, signal):
        output = signal.copy()
        
        for voice in range(self.voices):
            # Process each voice
            buffer = self._buffers[voice]
            pos = self._positions[voice]
            
            for i in range(len(signal)):
                # Calculate modulated delay
                mod_delay = int(self.depths[voice] * 
                              (np.sin(2 * np.pi * self.rates[voice] * self.phases[voice]) + 1) * 
                              50)
                read_pos = (pos - mod_delay) % len(buffer)
                
                # Mix delayed signal
                output[i] += buffer[read_pos] * 0.3
                buffer[pos] = signal[i]
                
                # Update positions
                pos = (pos + 1) % len(buffer)
                self.phases[voice] += 1.0 / 44100
            
            self._positions[voice] = pos
            
        return output / (self.voices + 1)  # Normalize output

def create_effect(effect_type):
    """Factory function to create effects"""
    effects = {
        'reverb': Reverb,
        'distortion': Distortion,
        'delay': Delay,
        'flanger': Flanger,
        'chorus': Chorus
    }
    return effects[effect_type]() if effect_type in effects else None

def get_cc_mapping():
    """Return MIDI CC mapping for effects"""
    return {
        102: 'reverb',
        103: 'distortion',
        104: 'delay',
        105: 'flanger',
        106: 'chorus'
    }
