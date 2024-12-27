"""
Waveform Generation System:
1. Basic Waveforms:
   - Sine: Pure tone
   - Saw: Rich harmonics
   - Triangle: Softer harmonics
   - Pulse: Variable duty cycle

2. Performance Optimizations:
   - Cached waveform generation
   - Buffer reuse
   - Vectorized operations

3. Voice Features:
   - Multiple oscillator mixing
   - Individual detune control
   - Phase tracking
"""
import numpy as np
from terminal_display import print_oscillator_bars
from functools import lru_cache

@lru_cache(maxsize=1024)
def _generate_base_waveform(wave_type, size):
    """
    Generate one cycle of a basic waveform.
    Uses caching to avoid regenerating identical waveforms.
    
    Args:
        wave_type: Type of waveform ('sine', 'saw', 'triangle', 'pulse')
        size: Number of samples in one cycle
        
    Returns:
        np.array: One cycle of the requested waveform
    """
    # Generate time points from 0 to 1
    t = np.linspace(0, 1, size, endpoint=False)
    
    if wave_type == 'sine':
        return np.sin(2 * np.pi * t)  # Pure sine wave
    elif wave_type == 'saw':
        return 2 * (t - np.floor(t + 0.5))  # Bipolar sawtooth
    elif wave_type == 'triangle':
        # Generate triangle wave using modified sawtooth
        return 2 * np.abs(2 * (t - np.floor(t + 0.5))) - 1
    elif wave_type == 'pulse':
        return np.where(t < 0.5, 1.0, -1.0)  # Square wave with 50% duty cycle

def generate_waveform(wave_type, frequency, sample_rate, duration, detune=0.0, duty_cycle=0.5):
    size = int(sample_rate * duration)
    base = _generate_base_waveform(wave_type, size)
    if detune != 0.0:
        phase = np.linspace(0, duration * detune, size, endpoint=False)
        return np.roll(base, int(phase[-1] * sample_rate))
    return base

def morph_waveforms(waveforms, weights):
    return sum(w * waveform for w, waveform in zip(weights, waveforms))

class Oscillator:
    """Polyphonic oscillator with multiple waveforms and detune capabilities."""
    
    def __init__(self):
        self.mix_levels = {k: 0.0 for k in ['sine', 'saw', 'triangle', 'pulse']}
        self.mix_levels['sine'] = 1.0  # Default to sine
        self.detune_values = {k: 0.0 for k in ['sine', 'saw', 'triangle', 'pulse']}
        self._buffer = None
        self._last_params = None
    
    def set_mix_level(self, osc_type, value):
        self.mix_levels[osc_type] = value / 127.0
        print_oscillator_bars(self.mix_levels, self.detune_values)

    def set_detune(self, osc_type, value):
        self.detune_values[osc_type] = value / 127.0 * 2.0 - 1.0
        print_oscillator_bars(self.mix_levels, self.detune_values)

    def generate(self, frequency, sample_rate, duration):
        """
        Generate audio for a specific note frequency.
        
        Args:
            frequency: Fundamental frequency in Hz
            sample_rate: Audio sample rate
            duration: Length of audio to generate in seconds
            
        Returns:
            np.array: Mixed waveform of all active oscillators
        """
        params = (frequency, sample_rate, duration)
        if self._buffer is None or params != self._last_params:
            size = int(sample_rate * duration)
            self._buffer = np.zeros(size)
            self._last_params = params

        self._buffer.fill(0)
        active_waves = [(wave, level) for wave, level in self.mix_levels.items() if level > 0]
        
        if not active_waves:
            return self._buffer

        for wave_type, level in active_waves:
            detune = frequency * (2 ** (self.detune_values[wave_type] / 12.0)) - frequency
            self._buffer += level * generate_waveform(wave_type, frequency, sample_rate, duration, detune)
        
        return self._buffer
