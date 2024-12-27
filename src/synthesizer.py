import numpy as np
import sounddevice as sd
import queue

class Synthesizer:
    def __init__(self):
        self.sample_rate = 44100
        self.active_voices = {}
        self.event_queue = queue.Queue()
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

    def audio_callback(self, outdata, frames, time, status):
        outdata.fill(0)
        
        # Process events
        while not self.event_queue.empty():
            event = self.event_queue.get()
            if event[0] == 'note_on':
                _, note, velocity, freq = event
                if note not in self.active_voices:
                    self.active_voices[note] = Voice(freq, velocity)
                    self.active_voices[note].playing = True
            elif event[0] == 'note_off' and event[1] in self.active_voices:
                del self.active_voices[event[1]]

        # Generate audio
        for voice in list(self.active_voices.values()):
            phase_increment = 2 * np.pi * voice.freq / self.sample_rate
            t = (np.arange(frames) + voice.phase) * phase_increment
            outdata[:, 0] += 0.3 * (voice.velocity / 127.0) * np.sin(t)
            voice.phase = (voice.phase + frames) % self.sample_rate
                
        outdata[:, 0] = np.tanh(outdata[:, 0])

class Voice:
    def __init__(self, freq, velocity):
        self.freq = freq
        self.velocity = velocity
        self.playing = False
        self.phase = 0.0
