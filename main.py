from kivy.app import App
from kivymd.app import MDApp
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty
class LabHeaderWidget(BoxLayout):
    
    def change_screen(self, screen_name, text):
        self.ids.screen_manager.current = screen_name

        # Set the global current_mode property
        app = App.get_running_app()
        app.current_mode = text

        # Get the target screen instance
        target_screen = self.ids.screen_manager.get_screen(screen_name)

        # Check if the target screen has a 'receive_text' method
        if hasattr(target_screen, 'receive_text') and callable(target_screen.receive_text):
            target_screen.receive_text(text)
        else:
            print(f"The screen '{screen_name}' does not have a 'receive_text' method.")

class MainFrameWidget(BoxLayout):
    pass

class SolarControlApp(App):
    current_mode = StringProperty('')

if __name__ == "__main__":
    SolarControlApp().run()
