class EventHandler:
    def __init__(self, synthesizer):
        # Initialize with a synthesizer instance
        self.synthesizer = synthesizer

    def handle_event(self, event):
        # Handle incoming events and trigger synthesizer actions
        if event.type == 'note_on':
            self.note_on(event.note, event.velocity)
        elif event.type == 'note_off':
            self.note_off(event.note)

    def note_on(self, note, velocity):
        self.synthesizer.note_on(note, velocity)

    def note_off(self, note):
        self.synthesizer.note_off(note)
