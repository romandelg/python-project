import numpy as np
import sounddevice as sd
import queue

class Synthesizer:
    def __init__(self):
        self.sample_rate = 44100
        self.stream = None
        self.active_voices = {}
        self.event_queue = queue.Queue()

        # Start the audio stream immediately
        self.stream = sd.OutputStream(
            channels=1,
            callback=self.audio_callback,
            samplerate=self.sample_rate,
            blocksize=256
        )
        self.stream.start()

    def note_on(self, note, velocity):
        freq = 440.0 * (2.0 ** ((note - 69) / 12.0))
        self.event_queue.put(('note_on', note, velocity, freq))

    def note_off(self, note):
        self.event_queue.put(('note_off', note))

    def create_voice(self, freq, velocity):
        return Voice(freq, velocity)

    def audio_callback(self, outdata, frames, time, status):
        outdata.fill(0)

        # Process any pending events
        while not self.event_queue.empty():
            event = self.event_queue.get()
            if event[0] == 'note_on':
                _, note, velocity, freq = event
                if note not in self.active_voices:
                    voice = self.create_voice(freq, velocity)
                    self.active_voices[note] = voice
                    voice.start()
            elif event[0] == 'note_off':
                _, note = event
                if note in self.active_voices:
                    self.active_voices[note].stop()
                    del self.active_voices[note]

        # Generate audio for active voices
        for voice in list(self.active_voices.values()):
            if voice.playing:
                phase_increment = 2 * np.pi * voice.freq / self.sample_rate
                t = (np.arange(frames) + voice.phase) * phase_increment
                # Scale amplitude by velocity
                amplitude = 0.3 * (voice.velocity / 127.0)
                outdata[:, 0] += amplitude * np.sin(t)
                voice.phase = (voice.phase + frames) % self.sample_rate
                
        # Soft clip instead of hard clip
        outdata[:, 0] = np.tanh(outdata[:, 0])

class Voice:
    def __init__(self, freq, velocity):
        self.freq = freq
        self.velocity = velocity
        self.playing = False
        self.phase = 0.0

    def start(self):
        self.playing = True

    def stop(self):
        self.playing = False
