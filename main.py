from kivy.app import App
# from kivymd.app import MDApp
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty
class LabHeaderWidget(BoxLayout):
    
    def change_screen(self, screen_name, text):
        screen_manager = self.ids.screen_manager
        self.ids.screen_manager.current = screen_name

        # Set the global current_mode property
        app = App.get_running_app()
        app.current_mode = text
        # print(screen_name, text)
        current_screen = screen_manager.current_screen
        current_screen.call_close_camera()
        current_screen.haddle_off_get_data()
        current_screen.stop_fetch_loop()
        # if screen_name == "auto":
        #     current_screen.call_close_camera()
        # elif screen_name == "manual":
        #     current_screen.call_close_camera()
        # elif screen_name == "path_control":
        #     current_screen.call_close_camera()
        #     current_screen.haddle_off_get_data()
        # elif screen_manager == "description":
        #     current_screen.stop_fetch_loop()
        # Get the target screen instance
        # target_screen = self.ids.screen_manager.get_screen(screen_name)
        
        # Check if the target screen has a 'receive_text' method
        # if hasattr(target_screen, 'receive_text') and callable(target_screen.receive_text):
        #     target_screen.receive_text(text)
            # print("text => ",text)
        # else:
        #     print(f"The screen '{screen_name}' does not have a 'receive_text' method.")

class MainFrameWidget(BoxLayout):
    pass

class SolarControlApp(App):
    current_mode = StringProperty('')

if __name__ == "__main__":
    SolarControlApp().run()
