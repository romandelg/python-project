import numpy as np
from terminal_display import print_filter_values  # Import the new function

class LowPassFilter:
    def __init__(self):
        self.cutoff_freq = 1000.0  # Default cutoff frequency in Hz
        self.resonance = 0.5  # Default resonance (Q factor)
        self.sample_rate = 44100  # Default sample rate
        self.prev_output = 0.0

    def set_cutoff_freq(self, value):
        self.cutoff_freq = value
        print_filter_values(self.cutoff_freq, self.resonance)

    def set_resonance(self, value):
        self.resonance = value
        print_filter_values(self.cutoff_freq, self.resonance)

    def apply_filter(self, signal):
        alpha = self.cutoff_freq / (self.cutoff_freq + self.sample_rate)
        filtered_signal = np.zeros_like(signal)
        for i in range(len(signal)):
            self.prev_output = alpha * signal[i] + (1 - alpha) * self.prev_output
            filtered_signal[i] = self.prev_output
        return filtered_signal
