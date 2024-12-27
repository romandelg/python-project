import tkinter as tk
from tkinter import ttk

class SynthesizerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Synthesizer Parameters")
        self.root.geometry("600x800")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Create frames for each section
        self.osc_frame = self._create_section_frame("Oscillator Mix Levels")
        self.filter_frame = self._create_section_frame("Filter Parameters")
        self.adsr_frame = self._create_section_frame("ADSR Envelope")
        
        # Initialize progress bars
        self.osc_bars = self._create_osc_section()
        self.filter_bars = self._create_filter_section()
        self.adsr_bars = self._create_adsr_section()

    def on_closing(self):
        self.root.quit()
        self.root.destroy()

    def _create_section_frame(self, title):
        frame = ttk.LabelFrame(self.root, text=title, padding="10")
        frame.pack(fill="x", padx=10, pady=5)
        return frame

    def _create_osc_section(self):
        bars = {}
        labels = ['sine', 'saw', 'triangle', 'pulse']
        for i, label in enumerate(labels):
            lbl = ttk.Label(self.osc_frame, text=f"{label:8}")
            lbl.grid(row=i, column=0, padx=5)
            bar = ttk.Progressbar(self.osc_frame, length=200, mode='determinate')
            bar.grid(row=i, column=1, padx=5)
            value_label = ttk.Label(self.osc_frame, text="0.00")
            value_label.grid(row=i, column=2, padx=5)
            bars[label] = (bar, value_label)
        return bars

    def _create_filter_section(self):
        controls = {}
        labels = ['Cutoff', 'Resonance']
        for i, label in enumerate(labels):
            lbl = ttk.Label(self.filter_frame, text=f"{label:10}")
            lbl.grid(row=i, column=0, padx=5)
            bar = ttk.Progressbar(self.filter_frame, length=200, mode='determinate')
            bar.grid(row=i, column=1, padx=5)
            value_label = ttk.Label(self.filter_frame, text="0.00")
            value_label.grid(row=i, column=2, padx=5)
            controls[label.lower()] = (bar, value_label)
        return controls

    def _create_adsr_section(self):
        controls = {}
        labels = ['Attack', 'Decay', 'Sustain', 'Release']
        for i, label in enumerate(labels):
            lbl = ttk.Label(self.adsr_frame, text=f"{label:8}")
            lbl.grid(row=i, column=0, padx=5)
            bar = ttk.Progressbar(self.adsr_frame, length=200, mode='determinate')
            bar.grid(row=i, column=1, padx=5)
            value_label = ttk.Label(self.adsr_frame, text="0.00")
            value_label.grid(row=i, column=2, padx=5)
            controls[label.lower()] = (bar, value_label)
        return controls

    def update_oscillator(self, mix_levels):
        self.root.after(0, self._update_oscillator, mix_levels)
        
    def _update_oscillator(self, mix_levels):
        for osc_type, level in mix_levels.items():
            if osc_type in self.osc_bars:
                bar, label = self.osc_bars[osc_type]
                bar['value'] = level * 100
                label['text'] = f"{level:.2f}"

    def update_filter(self, cutoff_freq, resonance):
        self.root.after(0, self._update_filter, cutoff_freq, resonance)
        
    def _update_filter(self, cutoff_freq, resonance):
        self.filter_bars['cutoff'][0]['value'] = (cutoff_freq / 12700) * 100
        self.filter_bars['cutoff'][1]['text'] = f"{cutoff_freq:.0f}Hz"
        self.filter_bars['resonance'][0]['value'] = resonance * 100
        self.filter_bars['resonance'][1]['text'] = f"{resonance:.2f}"

    def update_adsr(self, attack, decay, sustain, release):
        self.root.after(0, self._update_adsr, attack, decay, sustain, release)
        
    def _update_adsr(self, attack, decay, sustain, release):
        values = {'attack': attack, 'decay': decay, 
                 'sustain': sustain, 'release': release}
        for param, value in values.items():
            bar, label = self.adsr_bars[param]
            bar['value'] = value * 100
            label['text'] = f"{value:.2f}"

    def start(self):
        self.root.mainloop()
