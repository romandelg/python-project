import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, Callable
import threading

@dataclass
class ModulationTarget:
    parameter: str
    min_value: float
    max_value: float
    current_value: float
    callback: Callable

class AudioModule:
    def __init__(self, name):
        self.name = name
        self.enabled = True
        self.bypass = False
        self.modulation_targets: Dict[str, ModulationTarget] = {}
        self.input_buffer = None
        self.output_buffer = None

    def add_modulation_target(self, name: str, min_val: float, max_val: float, callback: Callable):
        self.modulation_targets[name] = ModulationTarget(name, min_val, max_val, 0.0, callback)

    def set_parameter(self, param_name: str, value: float):
        if param_name in self.modulation_targets:
            target = self.modulation_targets[param_name]
            normalized = np.clip(value, target.min_value, target.max_value)
            target.current_value = normalized
            target.callback(normalized)

    def process(self, signal):
        if not self.enabled or self.bypass:
            return signal
        return self._process_audio(signal)

    def _process_audio(self, signal):
        # Override this method in derived classes
        return signal

class ADSRModule(AudioModule):
    def __init__(self, adsr):
        super().__init__("adsr")
        self.adsr = adsr
        self.note_on = False
        self.note_off = False

    def _process_audio(self, signal):
        result = self.adsr.apply_envelope(signal, self.note_on, self.note_off)
        self.note_on = False
        self.note_off = False
        return result

    def trigger_note_on(self):
        self.note_on = True

    def trigger_note_off(self):
        self.note_off = True

class AudioChainHandler:
    def __init__(self):
        self.chain = []
        self.mod_matrix = {}
        self._buffer = None
        self.effects_chain = []
        self.processing_lock = threading.Lock()

    def add_module(self, module, position=None):
        if position is None:
            self.chain.append(module)
        else:
            self.chain.insert(position, module)

    def remove_module(self, module_name):
        self.chain = [m for m in self.chain if m.name != module_name]

    def get_module(self, module_name):
        for module in self.chain:
            if module.name == module_name:
                return module
        return None

    def add_modulation_route(self, source: str, target_module: str, target_param: str, amount: float):
        if source not in self.mod_matrix:
            self.mod_matrix[source] = []
        self.mod_matrix[source].append((target_module, target_param, amount))

    def add_effect(self, effect_module):
        self.effects_chain.append(effect_module)

    def process_voice(self, voice, signal):
        """Process audio for a single voice through its module chain"""
        if self._buffer is None or len(self._buffer) != len(signal):
            self._buffer = np.zeros_like(signal)

        np.copyto(self._buffer, signal)
        
        # Apply voice-specific processing
        active_modules = [m for m in self.chain if m.enabled and not m.bypass]
        for module in active_modules:
            self._buffer = module.process(self._buffer)
            
        return self._buffer

    def process_audio(self, voices_output):
        """Process the mixed output through global effects"""
        if not self.effects_chain:
            return voices_output

        result = voices_output
        for effect in self.effects_chain:
            if effect.enabled and not effect.bypass:
                result = effect.process(result)
        
        return result

    def process_audio(self, signal):
        with self.processing_lock:
            try:
                if not self.chain:
                    return signal

                if self._buffer is None or len(self._buffer) != len(signal):
                    self._buffer = np.zeros_like(signal)

                active_modules = [m for m in self.chain if m.enabled and not m.bypass]
                if not active_modules:
                    return signal

                np.copyto(self._buffer, signal)
                for module in active_modules:
                    try:
                        self._buffer = module.process(self._buffer)
                    except Exception as e:
                        print(f"Module processing error: {e}")
                        continue
                
                return self._buffer
            except Exception as e:
                print(f"Audio chain processing error: {e}")
                return signal

    def bypass_module(self, module_name, bypass=True):
        module = self.get_module(module_name)
        if module:
            module.bypass = bypass

    def enable_module(self, module_name, enable=True):
        module = self.get_module(module_name)
        if module:
            module.enabled = enable

class Effect(AudioModule):
    """Base class for effects modules"""
    def __init__(self, name):
        super().__init__(name)
        self.wet = 1.0
        self.dry = 0.0
        self.add_modulation_target('wet', 0.0, 1.0, self.set_wet)
        self.add_modulation_target('dry', 0.0, 1.0, self.set_dry)

    def set_wet(self, value):
        self.wet = value

    def set_dry(self, value):
        self.dry = value

    def _process_audio(self, signal):
        wet_signal = self._process_effect(signal)
        return signal * self.dry + wet_signal * self.wet

    def _process_effect(self, signal):
        """Override this method in effect subclasses"""
        return signal
