import numpy as np
from terminal_display import print_oscillator_bars  # Import the new function

def generate_sine(frequency, sample_rate, duration, detune=0.0):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    return np.sin(2 * np.pi * (frequency + detune) * t)

def generate_sawtooth(frequency, sample_rate, duration, detune=0.0):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    return 2 * ((t * (frequency + detune)) - np.floor(t * (frequency + detune) + 0.5))

def generate_triangle(frequency, sample_rate, duration, detune=0.0):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    return 2 * np.abs(2 * ((t * (frequency + detune)) - np.floor(t * (frequency + detune) + 0.5))) - 1

def generate_pulse(frequency, sample_rate, duration, duty_cycle=0.5, detune=0.0):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    return np.where((t * (frequency + detune)) % 1 < duty_cycle, 1.0, -1.0)

def morph_waveforms(waveforms, weights):
    combined_wave = sum(w * waveform for w, waveform in zip(weights, waveforms))
    return combined_wave

class Oscillator:
    def __init__(self):
        self.mix_levels = {
            'sine': 1.0,    # CC 14
            'saw': 0.0,     # CC 15
            'triangle': 0.0, # CC 16
            'pulse': 0.0    # CC 17
        }
        self.detune_values = {
            'sine': 0.0,    # CC 26
            'saw': 0.0,     # CC 27
            'triangle': 0.0, # CC 28
            'pulse': 0.0    # CC 29
        }
    
    def set_mix_level(self, osc_type, value):
        self.mix_levels[osc_type] = value / 127.0
        print_oscillator_bars(self.mix_levels, self.detune_values)

    def set_detune(self, osc_type, value):
        self.detune_values[osc_type] = value / 127.0 * 2.0 - 1.0  # Scale to -1 to +1 semitone
        print_oscillator_bars(self.mix_levels, self.detune_values)

    def _print_mix_levels(self):
        print("\n=== Oscillator Mix Levels ===")
        print("Type     Level   Visualization")
        print("-" * 50)
        for osc_type, level in self.mix_levels.items():
            bars = int(level * 20)
            percentage = int(level * 100)
            print(f"{osc_type:8} {percentage:3d}%  [{'█' * bars}{' ' * (20 - bars)}]")
        print("-" * 50)
        print(f"Total mix: {sum(self.mix_levels.values()):.2f}\n")

    def print_oscillator_bars(self):
        print_oscillator_bars(self.mix_levels, self.detune_values)

    def generate(self, frequency, sample_rate, duration):
        sine_wave = generate_sine(frequency * (2 ** (self.detune_values['sine'] / 12.0)), sample_rate, duration)
        saw_wave = generate_sawtooth(frequency * (2 ** (self.detune_values['saw'] / 12.0)), sample_rate, duration)
        triangle_wave = generate_triangle(frequency * (2 ** (self.detune_values['triangle'] / 12.0)), sample_rate, duration)
        pulse_wave = generate_pulse(frequency * (2 ** (self.detune_values['pulse'] / 12.0)), sample_rate, duration, 0.5)

        waveforms = [sine_wave, saw_wave, triangle_wave, pulse_wave]
        weights = [self.mix_levels['sine'], self.mix_levels['saw'], 
                  self.mix_levels['triangle'], self.mix_levels['pulse']]

        return morph_waveforms(waveforms, weights)
