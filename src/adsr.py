import numpy as np
from terminal_display import print_adsr_values  # Import the new function

class ADSR:
    def __init__(self):
        self.attack = 0.1
        self.decay = 0.1
        self.sustain = 0.7
        self.release = 0.1
        self.sample_rate = 44100
        self.current_level = 0.0
        self.current_state = 'off'
        self.time_in_state = 0

    def set_attack(self, value):
        self.attack = value
        print_adsr_values(self.attack, self.decay, self.sustain, self.release)

    def set_decay(self, value):
        self.decay = value
        print_adsr_values(self.attack, self.decay, self.sustain, self.release)

    def set_sustain(self, value):
        self.sustain = value
        print_adsr_values(self.attack, self.decay, self.sustain, self.release)

    def set_release(self, value):
        self.release = value
        print_adsr_values(self.attack, self.decay, self.sustain, self.release)

    def note_on(self):
        self.current_state = 'attack'
        self.time_in_state = 0

    def note_off(self):
        self.current_state = 'release'
        self.time_in_state = 0

    def get_next_value(self, samples):
        if self.current_state == 'off':
            return 0.0
        
        time_step = samples / self.sample_rate
        self.time_in_state += time_step

        if self.current_state == 'attack':
            if self.time_in_state >= self.attack:
                self.current_state = 'decay'
                self.time_in_state = 0
                return 1.0
            return self.time_in_state / self.attack

        elif self.current_state == 'decay':
            if self.time_in_state >= self.decay:
                self.current_state = 'sustain'
                return self.sustain
            decay_progress = self.time_in_state / self.decay
            return 1.0 - (1.0 - self.sustain) * decay_progress

        elif self.current_state == 'sustain':
            return self.sustain

        elif self.current_state == 'release':
            if self.time_in_state >= self.release:
                self.current_state = 'off'
                return 0.0
            return self.sustain * (1.0 - self.time_in_state / self.release)

    def apply_envelope(self, signal, note_on=False, note_off=False):
        if note_on:
            self.note_on()
        elif note_off:
            self.note_off()

        envelope = np.linspace(self.current_level, 
                             self.get_next_value(len(signal)), 
                             len(signal))
        self.current_level = envelope[-1]
        return signal * envelope
