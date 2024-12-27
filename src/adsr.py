class ADSR:
    def __init__(self):
        self.attack = 0.1
        self.decay = 0.1
        self.sustain = 0.7
        self.release = 0.1

    def set_attack(self, value):
        self.attack = value
        self._print_adsr_value('Attack', value)

    def set_decay(self, value):
        self.decay = value
        self._print_adsr_value('Decay', value)

    def set_sustain(self, value):
        self.sustain = value
        self._print_adsr_value('Sustain', value)

    def set_release(self, value):
        self.release = value
        self._print_adsr_value('Release', value)

    def _print_adsr_value(self, stage, value):
        bars = int(value * 20)
        percentage = int(value * 100)
        print(f"{stage:8} {percentage:3d}%  [{'█' * bars}{' ' * (20 - bars)}]")

    def apply_envelope(self, signal):
        # Apply the ADSR envelope to the signal
        # This is a placeholder implementation
        return signal
