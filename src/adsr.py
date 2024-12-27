from terminal_display import print_adsr_values  # Import the new function

class ADSR:
    def __init__(self):
        self.attack = 0.1
        self.decay = 0.1
        self.sustain = 0.7
        self.release = 0.1

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

    def apply_envelope(self, signal):
        # Apply the ADSR envelope to the signal
        # This is a placeholder implementation
        return signal
