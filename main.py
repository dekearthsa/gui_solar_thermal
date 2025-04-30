from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty


class LabHeaderWidget(BoxLayout):
    def change_screen(self, screen_name, text):
        screen_manager = self.ids.screen_manager
        self.ids.screen_manager.current = screen_name
        app = App.get_running_app()
        app.current_mode = text
        current_screen = screen_manager.current_screen
        current_screen.call_close_camera()
        current_screen.haddle_off_get_data()
        current_screen.stop_fetch_loop()

class MainFrameWidget(BoxLayout):
    pass

class SolarControlApp(App):
    current_mode = StringProperty('')

if __name__ == '__main__':
    # Start Flask in a separate thread
    # flask_thread = Thread(target=run_flask, daemon=True)
    # flask_thread.start()
    SolarControlApp().run()