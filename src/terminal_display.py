def print_oscillator_bars(mix_levels):
    print("\n=== Oscillator Values ===")
    for osc_type, level in mix_levels.items():
        bars = int(level * 20)
        print(f"{osc_type:8} [{'█' * bars}{' ' * (20 - bars)}] {level:.2f}")
    print("-" * 50)

def print_filter_values(cutoff_freq, resonance):
    print("\n=== Low Pass Filter Values ===")
    print(f"Cutoff Frequency: {cutoff_freq:.2f} Hz")
    print(f"Resonance: {resonance:.2f}")
    print("-" * 50)

def print_adsr_values(attack, decay, sustain, release):
    print("\n=== ADSR Values ===")
    stages = {'Attack': attack, 'Decay': decay, 'Sustain': sustain, 'Release': release}
    for stage, value in stages.items():
        bars = int(value * 20)
        print(f"{stage:8} [{'█' * bars}{' ' * (20 - bars)}] {value:.2f}")
    print("-" * 50)

def print_all_values(mix_levels, cutoff_freq, resonance, attack, decay, sustain, release):
    print("\n=== All Values ===")
    print_oscillator_bars(mix_levels)
    print_filter_values(cutoff_freq, resonance)
    print_adsr_values(attack, decay, sustain, release)
    print("=" * 50)
