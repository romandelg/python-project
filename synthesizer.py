import threading
import numpy as np

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
        self.voice_lock = threading.Lock()
        self.sample_rate = 44100
        self.buffer_size = 1024
        self.running = True

    def note_on(self, note, velocity):
        voice = self.create_voice(note, velocity)
        with self.voice_lock:
            self.active_voices.append(voice)
        voice.start()

    def note_off(self, note):
        with self.voice_lock:
            for voice in self.active_voices:
                if voice.note == note:
                    voice.stop()
            self.active_voices = [voice for voice in self.active_voices if voice.note != note]

    def create_voice(self, note, velocity):
        return Voice(note, velocity)

    def process_audio(self):
        """Process audio in a thread-safe manner"""
        while self.running:
            with self.voice_lock:
                # Create an empty buffer for mixing voices
                mixed_output = np.zeros(self.buffer_size)
                
                # Process each active voice
                for voice in self.active_voices:
                    if voice.playing:
                        # Generate audio for this voice
                        # This is a placeholder - implement actual voice processing
                        voice_output = np.zeros(self.buffer_size)
                        mixed_output += voice_output
                
                # Return the mixed output
                return mixed_output

    def stop(self):
        """Safely stop audio processing"""
        self.running = False
