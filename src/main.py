import mido
import numpy as np
import sounddevice as sd
import threading
import time

class MIDIHandler:
    def __init__(self):
        self.synth = Synthesizer()
        
    def scan_devices(self):
        print("Available MIDI input ports:")
        for port in mido.get_input_names():
            print(f"- {port}")
            
    def start(self, port_name=None):
        if not port_name:
            available_ports = mido.get_input_names()
            if not available_ports:
                print("No MIDI devices found!")
                return
            port_name = available_ports[0]
            
        try:
            with mido.open_input(port_name) as midi_port:
                print(f"Listening on {port_name}")
                for message in midi_port:
                    self._handle_message(message)
        except KeyboardInterrupt:
            print("\nStopping...")
            
    def _handle_message(self, message):
        if message.type == 'note_on':
            freq = 440 * (2 ** ((message.note - 69) / 12))
            if message.velocity > 0:
                self.synth.note_on(freq)
            else:
                self.synth.note_off()
        elif message.type == 'note_off':
            self.synth.note_off()

class Synthesizer:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        self.playing = False
        self.stream = None
        self.current_freq = 0
        
    def audio_callback(self, outdata, frames, time, status):
        if self.playing:
            t = np.linspace(0, frames/self.sample_rate, frames, False)
            outdata[:, 0] = 0.5 * np.sin(2 * np.pi * self.current_freq * t)
        else:
            outdata.fill(0)
            
    def note_on(self, freq):
        self.current_freq = freq
        if not self.stream:
            self.stream = sd.OutputStream(
                channels=1,
                callback=self.audio_callback,
                samplerate=self.sample_rate
            )
            self.stream.start()
        self.playing = True
        
    def note_off(self):
        self.playing = False

def main():
    midi = MIDIHandler()
    midi.scan_devices()
    
    port_name = input("Enter MIDI device name (or press Enter for first available): ").strip()
    midi.start(port_name if port_name else None)

if __name__ == "__main__":
    main()