from gui_display import SynthesizerGUI

class TerminalDisplay:
    _instance = None
    _gui = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def set_gui(cls, gui):
        cls._gui = gui

    def print_oscillator_bars(self, mix_levels, detune_values):
        if self._gui:
            self._gui.update_oscillator(mix_levels, detune_values)

    def print_filter_values(self, cutoff_freq, resonance):
        if self._gui:
            self._gui.update_filter(cutoff_freq, resonance)

    def print_adsr_values(self, attack, decay, sustain, release):
        if self._gui:
            self._gui.update_adsr(attack, decay, sustain, release)

    def print_all_values(self, mix_levels, detune_values, cutoff_freq, resonance, attack, decay, sustain, release):
        if self._gui:
            self._gui.update_oscillator(mix_levels, detune_values)
            self._gui.update_filter(cutoff_freq, resonance)
            self._gui.update_adsr(attack, decay, sustain, release)

terminal_display = TerminalDisplay.get_instance()

def print_oscillator_bars(mix_levels, detune_values):
    terminal_display.print_oscillator_bars(mix_levels, detune_values)

def print_filter_values(cutoff_freq, resonance):
    terminal_display.print_filter_values(cutoff_freq, resonance)

def print_adsr_values(attack, decay, sustain, release):
    terminal_display.print_adsr_values(attack, decay, sustain, release)

def print_all_values(*args):
    terminal_display.print_all_values(*args)

def start_gui():
    gui = SynthesizerGUI()
    TerminalDisplay.set_gui(gui)
    gui.start()

def print_effect_values(effect_name, enabled, dry_wet):
    if TerminalDisplay._gui:
        TerminalDisplay._gui.update_effect(effect_name, enabled, dry_wet)
