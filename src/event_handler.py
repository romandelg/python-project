class EventHandler:
    def __init__(self, synthesizer, adsr):
        self.synthesizer = synthesizer
        self.adsr = adsr

    def handle_event(self, event):
        if event.type == 'note_on':
            self.synthesizer.note_on(event.note)  # Remove velocity parameter
        elif event.type == 'note_off':
            self.synthesizer.note_off(event.note)
        elif event.type == 'control_change':
            self.handle_control_change(event.control, event.value)

    def handle_control_change(self, control, value):
        if control in [14, 15, 16, 17,  # Oscillator mix
                      26, 27, 28, 29,   # Oscillator detune
                      18, 19, 20, 21,   # ADSR
                      22, 23]:          # Filter
            self.synthesizer.control_change(control, value)
        else:
            self.synthesizer.oscillator.set_mix_level(control, value)
