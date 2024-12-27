class AudioModule:
    def __init__(self, name):
        self.name = name
        self.enabled = True
        self.bypass = False

    def process(self, signal):
        if not self.enabled or self.bypass:
            return signal
        return self._process_audio(signal)

    def _process_audio(self, signal):
        # Override this method in derived classes
        return signal

class AudioChainHandler:
    def __init__(self):
        self.chain = []

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

    def process_audio(self, signal):
        for module in self.chain:
            signal = module.process(signal)
        return signal

    def bypass_module(self, module_name, bypass=True):
        module = self.get_module(module_name)
        if module:
            module.bypass = bypass

    def enable_module(self, module_name, enable=True):
        module = self.get_module(module_name)
        if module:
            module.enabled = enable
