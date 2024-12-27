import numpy as np
from terminal_display import print_oscillator_bars

def generate_waveform(wave_type, frequency, sample_rate, duration, detune=0.0, duty_cycle=0.5):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    freq = frequency + detune
    if wave_type == 'sine':
        return np.sin(2 * np.pi * freq * t)
    elif wave_type == 'saw':
        return 2 * (t * freq - np.floor(t * freq + 0.5))
    elif wave_type == 'triangle':
        return 2 * np.abs(2 * (t * freq - np.floor(t * freq + 0.5))) - 1
    elif wave_type == 'pulse':
        return np.where((t * freq) % 1 < duty_cycle, 1.0, -1.0)

def morph_waveforms(waveforms, weights):
    return sum(w * waveform for w, waveform in zip(weights, waveforms))

class Oscillator:
    def __init__(self):
        self.mix_levels = {'sine': 1.0, 'saw': 0.0, 'triangle': 0.0, 'pulse': 0.0}
        self.detune_values = {'sine': 0.0, 'saw': 0.0, 'triangle': 0.0, 'pulse': 0.0}
    
    def set_mix_level(self, osc_type, value):
        self.mix_levels[osc_type] = value / 127.0
        print_oscillator_bars(self.mix_levels, self.detune_values)

    def set_detune(self, osc_type, value):
        self.detune_values[osc_type] = value / 127.0 * 2.0 - 1.0
        print_oscillator_bars(self.mix_levels, self.detune_values)

    def generate(self, frequency, sample_rate, duration):
        waveforms = [
            generate_waveform('sine', frequency, sample_rate, duration, frequency * (2 ** (self.detune_values['sine'] / 12.0)) - frequency),
            generate_waveform('saw', frequency, sample_rate, duration, frequency * (2 ** (self.detune_values['saw'] / 12.0)) - frequency),
            generate_waveform('triangle', frequency, sample_rate, duration, frequency * (2 ** (self.detune_values['triangle'] / 12.0)) - frequency),
            generate_waveform('pulse', frequency, sample_rate, duration, 0.5, frequency * (2 ** (self.detune_values['pulse'] / 12.0)) - frequency)
        ]
        weights = [self.mix_levels['sine'], self.mix_levels['saw'], self.mix_levels['triangle'], self.mix_levels['pulse']]
        return morph_waveforms(waveforms, weights)
