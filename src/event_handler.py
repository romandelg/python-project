class EventHandler:
    def __init__(self, synthesizer, adsr):
        self.synthesizer = synthesizer
        self.adsr = adsr

    def handle_event(self, event):
        if event.type == 'note_on':
            self.synthesizer.note_on(event.note, event.velocity)
        elif event.type == 'note_off':
            self.synthesizer.note_off(event.note)
        elif event.type == 'control_change':
            self.handle_control_change(event.control, event.value)

    def handle_control_change(self, control, value):
        if control == 18:
            self.adsr.set_attack(value / 127.0)
        elif control == 19:
            self.adsr.set_sustain(value / 127.0)
        elif control == 20:
            self.adsr.set_decay(value / 127.0)
        elif control == 21:
            self.adsr.set_release(value / 127.0)
        elif control == 22:
            self.synthesizer.filter.set_cutoff_freq(value * 100.0)  # Scale to 0-12700 Hz
        elif control == 23:
            self.synthesizer.filter.set_resonance(value / 127.0)
