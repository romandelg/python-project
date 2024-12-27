"""
MIDI Event Handler and Parameter Mapping System
--------------------------------------------
Central nervous system of the synthesizer that routes MIDI messages
to appropriate components and manages parameter updates.

Control Change (CC) Mapping:
- Oscillator Mix (CC 14-17):
  * 14: Sine level
  * 15: Saw level
  * 16: Triangle level
  * 17: Pulse level

- Oscillator Detune (CC 26-29):
  * 26: Sine detune
  * 27: Saw detune
  * 28: Triangle detune
  * 29: Pulse detune

- ADSR Controls (CC 18-21):
  * 18: Attack time
  * 19: Decay time
  * 20: Sustain level
  * 21: Release time

- Filter Controls (CC 22-23):
  * 22: Cutoff frequency (exponential mapping)
  * 23: Resonance

- Effects Controls (CC 102-106):
  * 102: Reverb mix
  * 103: Distortion amount
  * 104: Delay time/feedback
  * 105: Flanger rate/depth
  * 106: Chorus mix
"""

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
