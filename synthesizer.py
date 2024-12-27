class Voice:
    def __init__(self, note, velocity):
        self.note = note
        self.velocity = velocity
        self.playing = False
        self.phase = 0.0

    def start(self):
        self.playing = True

    def stop(self):
        self.playing = False

class Synthesizer:
    def __init__(self):
        self.active_voices = []

    def note_on(self, note, velocity):
        voice = self.create_voice(note, velocity)
        self.active_voices.append(voice)
        voice.start()

    def note_off(self, note):
        for voice in self.active_voices:
            if voice.note == note:
                voice.stop()
        self.active_voices = [voice for voice in self.active_voices if voice.note != note]

    def create_voice(self, note, velocity):
        return Voice(note, velocity)
