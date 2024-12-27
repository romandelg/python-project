"""MIDI Event Handler and Parameter Mapping System"""
# No imports needed - all dependencies are passed through __init__

class EventHandler:
    def __init__(self, synthesizer, adsr):
        """
        Initialize event handler with references to main components.
        Args:
            synthesizer: Main synthesizer instance
            adsr: Envelope generator instance
        """
        self.synthesizer = synthesizer  # Main synth engine
        self.adsr = adsr                # Envelope generator

    def handle_event(self, event):
        """
        Process incoming MIDI events and route to appropriate handlers.
        Supports note on/off and control change messages.
        
        Args:
            event: MIDI message containing type and parameters
        """
        if event.type == 'note_on':
            self.synthesizer.note_on(event.note)  # Remove velocity parameter
        elif event.type == 'note_off':
            self.synthesizer.note_off(event.note)
        elif event.type == 'control_change':
            self.handle_control_change(event.control, event.value)

    def handle_control_change(self, control, value):
        """
        Route control change messages to appropriate parameters.
        Uses predefined CC mapping for parameter updates.
        
        Args:
            control: MIDI CC number (0-127)
            value: Control value (0-127)
        """
        if control in [14, 15, 16, 17,  # Oscillator mix
                      26, 27, 28, 29,   # Oscillator detune
                      18, 19, 20, 21,   # ADSR
                      22, 23]:          # Filter
            self.synthesizer.control_change(control, value)
        else:
            self.synthesizer.oscillator.set_mix_level(control, value)
