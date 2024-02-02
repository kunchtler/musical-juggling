import ipytone

class Audio():
    def __init__(self):
        self.synth = ipytone.PolySynth().to_destination()

    def play(self, note, duration=0.2):
        self.synth.trigger_attack_release(note, duration)

    def pause(self):
        self.synth.release_all()
