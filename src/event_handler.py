class EventHandler:
    def __init__(self, synthesizer):
        self.synthesizer = synthesizer

    def handle_event(self, event):
        if event.type == 'note_on':
            self.synthesizer.note_on(event.note, event.velocity)
        elif event.type == 'note_off':
            self.synthesizer.note_off(event.note)
        elif event.type == 'control_change':
            self.synthesizer.control_change(event.control, event.value)
