import numpy as np

def generate_sine(frequency, sample_rate, duration):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    return np.sin(2 * np.pi * frequency * t)

def generate_sawtooth(frequency, sample_rate, duration):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    return 2 * (t * frequency - np.floor(t * frequency + 0.5))

def generate_triangle(frequency, sample_rate, duration):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    return 2 * np.abs(2 * (t * frequency - np.floor(t * frequency + 0.5))) - 1

def generate_pulse(frequency, sample_rate, duration, duty_cycle=0.5):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    return np.where((t * frequency) % 1 < duty_cycle, 1.0, -1.0)

def morph_waveforms(waveforms, weights):
    normalized_weights = np.array(weights) / sum(weights)
    combined_wave = sum(w * waveform for w, waveform in zip(normalized_weights, waveforms))
    return combined_wave

class Oscillator:
    def __init__(self):
        self.mix_levels = {
            'sine': 1.0,    # CC 14
            'saw': 0.0,     # CC 15
            'triangle': 0.0, # CC 16
            'pulse': 0.0    # CC 17
        }
    
    def set_mix_level(self, osc_type, value):
        self.mix_levels[osc_type] = value / 127.0
        self._print_mix_levels()

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

    def generate(self, frequency, sample_rate, duration):
        sine_wave = generate_sine(frequency, sample_rate, duration)
        saw_wave = generate_sawtooth(frequency, sample_rate, duration)
        triangle_wave = generate_triangle(frequency, sample_rate, duration)
        pulse_wave = generate_pulse(frequency, sample_rate, duration)

        waveforms = [sine_wave, saw_wave, triangle_wave, pulse_wave]
        weights = [self.mix_levels['sine'], self.mix_levels['saw'], self.mix_levels['triangle'], self.mix_levels['pulse']]

        return morph_waveforms(waveforms, weights)
