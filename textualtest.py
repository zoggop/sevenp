from textual.app import App, ComposeResult
from textual.widgets import Footer, TextArea, Input

my_list = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i']
my_text = ''
columns = 3
for first, second, third in zip(
    my_list[::columns], my_list[1::columns], my_list[2::columns]
): my_text += f'{first: <10}{second: <10}{third}\n'

class PasswordApp(App):
    """A Textual app to manage stopwatches."""

    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Input()
        yield TextArea(my_text)
        yield Footer()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark


if __name__ == "__main__":
    app = PasswordApp()
    app.run()