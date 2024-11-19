from kivy.uix.widget import Widget
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.properties import StringProperty

class BlinkSpot(Widget):
    auto_text = StringProperty("Auto off")
    def __init__(self, **kwargs):
        super(BlinkSpot, self).__init__(**kwargs)
        # self.is_blink = "off"
        self.anim = None
        self.bind(auto_text=self.on_auto_text)
        # Initialize the blink based on the initial auto_text
        Clock.schedule_once(lambda dt: self.on_auto_text(self, self.auto_text))

    def on_auto_text(self, instance, value):
        # print(value)
        if value == "Auto on":
            self.start_blinking()
            # self.is_blink = "on"
        else:
            self.stop_blinking()
            # self.is_blink = "off"

    def start_blinking(self):
        if not self.anim:
            self.anim = Animation(opacity=0, duration=0.5) + Animation(opacity=1, duration=0.5)
            self.anim.bind(on_complete=lambda *args: self.start_blinking())
            self.anim.start(self)

    def stop_blinking(self):
        if self.anim:
            self.anim.cancel(self)
            self.anim = None
        self.opacity = 0


