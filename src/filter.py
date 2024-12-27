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
        self._prev_cutoff = None
        self._prev_resonance = None
        self._coefficient_smooth = 0.99
        self._max_coefficient_change = 0.1
        self._update_coefficients()

    def _update_coefficients(self):
        try:
            # Normalize and bound frequencies
            w0 = 2.0 * np.pi * np.clip(self.cutoff_freq, 20.0, self.sample_rate/2.1) / self.sample_rate
            resonance = np.clip(self.resonance, 0.1, 10.0)
            alpha = np.sin(w0) / (2.0 * resonance)
            cos_w0 = np.cos(w0)
            
            # Calculate new coefficients
            a0 = 1.0 + alpha
            new_a1 = (-2.0 * cos_w0) / a0
            new_b0 = ((1.0 - cos_w0) / 2.0) / a0
            new_b1 = (1.0 - cos_w0) / a0

            # Smooth coefficient changes
            if self._prev_cutoff is not None:
                self.a1 = self._smooth_parameter(self.a1, new_a1)
                self.b0 = self._smooth_parameter(self.b0, new_b0)
                self.b1 = self._smooth_parameter(self.b1, new_b1)
            else:
                self.a1 = new_a1
                self.b0 = new_b0
                self.b1 = new_b1

            # Store current parameters
            self._prev_cutoff = self.cutoff_freq
            self._prev_resonance = self.resonance

        except Exception as e:
            print(f"Filter coefficient update error: {e}")
            self.reset()

    def _smooth_parameter(self, old_value, new_value):
        change = new_value - old_value
        if abs(change) > self._max_coefficient_change:
            change = np.sign(change) * self._max_coefficient_change
        return old_value + change * (1.0 - self._coefficient_smooth)

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
        """Reset filter state and coefficients"""
        self._prev_x = 0.0
        self._prev_y = 0.0
        self._dc_block = 0.0
        self.a1 = 0.0
        self.b0 = 0.5
        self.b1 = 0.5
        self._prev_cutoff = None
        self._prev_resonance = None
