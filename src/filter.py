import numpy as np
from terminal_display import print_filter_values

class LowPassFilter:
    def __init__(self):
        self.cutoff_freq = 1000.0
        self.resonance = 0.5
        self.sample_rate = 44100
        # Filter coefficients
        self.a1 = 0.0
        self.b0 = 0.0
        self.b1 = 0.0
        self._prev_x = 0.0
        self._prev_y = 0.0
        self._dc_block = 0.0
        self._dc_block_factor = 0.995
        self._update_coefficients()

    def _update_coefficients(self):
        # Normalize cutoff frequency
        w0 = 2.0 * np.pi * np.clip(self.cutoff_freq, 20.0, self.sample_rate/2.1) / self.sample_rate
        alpha = np.sin(w0) / (2.0 * np.clip(self.resonance, 0.1, 10.0))
        cos_w0 = np.cos(w0)
        
        # Calculate filter coefficients
        a0 = 1.0 + alpha
        self.a1 = np.clip((-2.0 * cos_w0) / a0, -1.0, 1.0)
        self.b0 = np.clip(((1.0 - cos_w0) / 2.0) / a0, -1.0, 1.0)
        self.b1 = np.clip((1.0 - cos_w0) / a0, -1.0, 1.0)

    def set_cutoff_freq(self, value):
        self.cutoff_freq = np.clip(value, 20.0, self.sample_rate/2)
        self._update_coefficients()
        print_filter_values(self.cutoff_freq, self.resonance)

    def set_resonance(self, value):
        self.resonance = np.clip(value, 0.1, 10.0)
        self._update_coefficients()
        print_filter_values(self.cutoff_freq, self.resonance)

    def apply_filter(self, signal):
        output = np.zeros_like(signal, dtype=np.float64)
        
        for i in range(len(signal)):
            # DC blocking
            input_sample = signal[i] - self._dc_block
            self._dc_block = self._dc_block * self._dc_block_factor + input_sample * (1.0 - self._dc_block_factor)
            
            # Apply difference equation with bounds checking
            output[i] = np.clip(
                self.b0 * input_sample + 
                self.b1 * self._prev_x - 
                self.a1 * self._prev_y,
                -1.0, 1.0
            )
            
            # Update delay registers
            self._prev_x = input_sample
            self._prev_y = output[i]
            
        return output

    def reset(self):
        """Reset filter state"""
        self._prev_x = 0.0
        self._prev_y = 0.0
