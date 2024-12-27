from gui_display import SynthesizerGUI

gui = SynthesizerGUI()

def print_oscillator_bars(mix_levels, detune_values):
    gui.update_oscillator(mix_levels, detune_values)

def print_filter_values(cutoff_freq, resonance):
    gui.update_filter(cutoff_freq, resonance)

def print_adsr_values(attack, decay, sustain, release):
    gui.update_adsr(attack, decay, sustain, release)

def print_all_values(mix_levels, detune_values, cutoff_freq, resonance, attack, decay, sustain, release):
    gui.update_oscillator(mix_levels, detune_values)
    gui.update_filter(cutoff_freq, resonance)
    gui.update_adsr(attack, decay, sustain, release)

def start_gui():
    gui.start()
