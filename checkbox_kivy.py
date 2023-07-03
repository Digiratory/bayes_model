# Program to learn how to make checkbox in kivy

# import kivy module
import kivy

# base Class of your App inherits from the App class.
# app:always refers to the instance of your application
from kivy.app import App

# The :class:`Widget` class is the base class
# required for creating Widgets.
from kivy.uix.widget import Widget

# The Label widget is for rendering text.
from kivy.uix.label import Label

# To use the checkbox must import it from this module
from kivy.uix.checkbox import CheckBox

# The GridLayout arranges children in a matrix.
from kivy.uix.gridlayout import GridLayout

import pandas as pd

def on_checkbox_active(checkbox, value):
    if value:
        print('The checkbox', checkbox, 'is active')
    else:
        print('The checkbox', checkbox, 'is inactive')


# Container class for the app's widgets
class check_box(GridLayout):

    def __init__(self, **kwargs):
        # super function can be used to gain access
        # to inherited methods from a parent or sibling class
        # that has been overwritten in a class object.
        super(check_box, self).__init__(**kwargs)

        # 2 columns in grid layout
        self.columns_names = read_data().columns
        self.cols = len(self.columns_names)


        # Add checkbox, widget and labels
        for i in self.columns_names:
            label = Label(text='blah blah ' * 1000, size_hint=(1, None))

            self.add_widget(label)


        for i in self.columns_names:
            self.add_widget(Label(text=i))
            for i in range(self.cols-1):
                self.active = CheckBox(active=True)
                self.active.bind(active=on_checkbox_active)
                self.add_widget(self.active)


# App derived from App class
class CheckBoxApp(App):
    def build(self):
        return check_box()


def read_data(path='data/tmp.csv'):
    data_input = pd.read_csv(path)
    return data_input

def generate_link_tabel(columns_names):
    return 1


# Run the app
if __name__ == '__main__':
    CheckBoxApp().run()