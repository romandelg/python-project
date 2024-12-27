import numpy as np
from terminal_display import print_filter_values  # Import the new function

class LowPassFilter:
    def __init__(self):
        self.cutoff_freq = 1000.0  # Default cutoff frequency in Hz
        self.resonance = 0.5  # Default resonance (Q factor)
        self.sample_rate = 44100  # Default sample rate
        self.prev_output = 0.0
        self._buffer = None
        self._last_alpha = None

    def set_cutoff_freq(self, value):
        self.cutoff_freq = value
        print_filter_values(self.cutoff_freq, self.resonance)

    def set_resonance(self, value):
        self.resonance = value
        print_filter_values(self.cutoff_freq, self.resonance)

    def apply_filter(self, signal):
        alpha = self.cutoff_freq / (self.cutoff_freq + self.sample_rate)
        
        if self._buffer is None or len(self._buffer) != len(signal):
            self._buffer = np.zeros_like(signal)
        
        if alpha != self._last_alpha:
            self._last_alpha = alpha
            self._coeffs = np.array([alpha, 1 - alpha])

        # Vectorized implementation
        self._buffer[0] = alpha * signal[0] + (1 - alpha) * self.prev_output
        self._buffer[1:] = alpha * signal[1:] + (1 - alpha) * signal[:-1]
        self.prev_output = self._buffer[-1]
        
        return self._buffer
