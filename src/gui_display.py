import tkinter as tk
from tkinter import ttk
import queue
import time
from .terminal_display import TerminalDisplay

"""
GUI System Architecture:
1. Display Sections:
   - Oscillator controls and visualization
   - Filter parameters
   - ADSR envelope
   - Effects controls

2. Update System:
   - Thread-safe queue
   - Rate-limited updates (30 FPS)
   - Event-driven parameter display

3. User Interface:
   - Real-time parameter visualization
   - Effect enable/disable toggles
   - Parameter value displays
"""

"""
Real-time Parameter Display System
--------------------------------
Provides visual feedback of synthesizer parameters.

Update System:
1. Parameters → Update Queue → GUI Thread → Visual Display
2. Rate-limited to 30 FPS for efficiency
3. Thread-safe operation
"""

class SynthesizerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.update_queue = queue.Queue()
        self.root.title("Event-Driven Synthesizer")
        self.root.geometry("600x800")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.osc_frame = self._create_section_frame("Oscillator Mix Levels")
        self.filter_frame = self._create_section_frame("Filter Parameters")
        self.adsr_frame = self._create_section_frame("ADSR Envelope")
        self.effects_frame = self._create_section_frame("Effects")
        
        self.osc_bars = self._create_osc_section()
        self.filter_bars = self._create_filter_section()
        self.adsr_bars = self._create_adsr_section()
        self.effects_controls = self._create_effects_section()
        
        self.running = True
        self.last_update = time.time()
        self.update_interval = 1/30  # 30 FPS max

    def on_closing(self):
        self.running = False
        try:
            self.root.quit()
            self.root.destroy()
        except:
            pass

    def is_running(self):
        return self.running

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
            detune_label = ttk.Label(self.osc_frame, text="±0.00st")
            detune_label.grid(row=i, column=3, padx=5)
            bars[label] = (bar, value_label, detune_label)
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

    def _create_effects_section(self):
        controls = {}
        effects = ['Reverb', 'Distortion', 'Delay', 'Flanger', 'Chorus']
        
        for i, effect in enumerate(effects):
            frame = ttk.Frame(self.effects_frame)
            frame.grid(row=i, column=0, sticky='ew', padx=5, pady=2)
            
            # Enable/Disable switch
            switch = ttk.Checkbutton(frame, text=effect)
            switch.grid(row=0, column=0, padx=5)
            
            # Dry/Wet control
            bar = ttk.Progressbar(frame, length=150, mode='determinate')
            bar.grid(row=0, column=1, padx=5)
            
            value_label = ttk.Label(frame, text="0.00")
            value_label.grid(row=0, column=2, padx=5)
            
            controls[effect.lower()] = (switch, bar, value_label)
        
        return controls

    def process_updates(self):
        """
        Process queued parameter updates at fixed rate.
        Prevents GUI overload from rapid parameter changes.
        """
        current_time = time.time()
        if current_time - self.last_update >= self.update_interval:
            # Process all pending updates in queue
            updates = self._collect_updates()
            self._apply_updates(updates)
            self.last_update = current_time

        # Schedule next update
        if self.running:
            self.root.after(10, self.process_updates)

    def _collect_updates(self):
        """Gather all pending updates from queue"""
        updates = {}
        try:
            while True:
                update_type, args = self.update_queue.get_nowait()
                updates[update_type] = args
        except queue.Empty:
            pass
        return updates

    def _apply_updates(self, updates):
        """Apply collected updates to GUI elements"""
        if 'oscillator' in updates:
            self._update_oscillator(*updates['oscillator'])
        if 'filter' in updates:
            self._update_filter(*updates['filter'])
        if 'adsr' in updates:
            self._update_adsr(*updates['adsr'])
        if 'effect' in updates:
            self._update_effect(*updates['effect'])

    def update_oscillator(self, mix_levels, detune_values):
        self.update_queue.put(('oscillator', (mix_levels, detune_values)))
        
    def _update_oscillator(self, mix_levels, detune_values):
        for osc_type, level in mix_levels.items():
            if osc_type in self.osc_bars:
                bar, level_label, detune_label = self.osc_bars[osc_type]
                bar['value'] = level * 100
                level_label['text'] = f"{level:.2f}"
                detune_label['text'] = f"±{abs(detune_values[osc_type]):.2f}st"

    def update_filter(self, cutoff_freq, resonance):
        self.update_queue.put(('filter', (cutoff_freq, resonance)))
        
    def _update_filter(self, cutoff_freq, resonance):
        self.filter_bars['cutoff'][0]['value'] = (cutoff_freq / 12700) * 100
        self.filter_bars['cutoff'][1]['text'] = f"{cutoff_freq:.0f}Hz"
        self.filter_bars['resonance'][0]['value'] = resonance * 100
        self.filter_bars['resonance'][1]['text'] = f"{resonance:.2f}"

    def update_adsr(self, attack, decay, sustain, release):
        self.update_queue.put(('adsr', (attack, decay, sustain, release)))
        
    def _update_adsr(self, attack, decay, sustain, release):
        values = {'attack': attack, 'decay': decay, 'sustain': sustain, 'release': release}
        for param, value in values.items():
            bar, label = self.adsr_bars[param]
            bar['value'] = value * 100
            label['text'] = f"{value:.2f}"

    def update_effect(self, effect_name, enabled, dry_wet):
        self.update_queue.put(('effect', (effect_name, enabled, dry_wet)))

    def _update_effect(self, effect_name, enabled, dry_wet):
        if effect_name in self.effects_controls:
            switch, bar, label = self.effects_controls[effect_name]
            switch.state(['selected' if enabled else '!selected'])
            bar['value'] = dry_wet * 100
            label['text'] = f"{dry_wet:.2f}"

    def start(self):
        self.process_updates()  # Start processing updates
        self.root.mainloop()

    def update_display(self, data):
        # Update GUI elements with new data
        pass
