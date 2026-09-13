from prompt_toolkit import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import HSplit, Layout, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.styles import Style


def multi_select(message, options):
    if not options:
        return []

    selected = set()
    cursor = 0
    count = len(options)

    bindings = KeyBindings()

    @bindings.add("up")
    def _move_up(event):
        nonlocal cursor
        cursor = (cursor - 1) % count

    @bindings.add("down")
    def _move_down(event):
        nonlocal cursor
        cursor = (cursor + 1) % count

    @bindings.add(" ")
    def _toggle(event):
        _, value, disabled = options[cursor]

        if disabled:
            return

        if value in selected:
            selected.discard(value)
        else:
            selected.add(value)

    @bindings.add("enter")
    def _confirm(event):
        event.app.exit(result=list(selected))

    @bindings.add("c-c")
    @bindings.add("escape")
    def _cancel(event):
        event.app.exit(result=None)

    def _render():
        lines = [("class:question", f"? {message}\n")]

        for index, (label, value, disabled) in enumerate(options):
            pointer = "> " if index == cursor else "  "
            mark = "[x]" if value in selected else "[ ]"

            line_style = (
                "class:disabled"
                if disabled
                else ("class:current" if index == cursor else "")
            )

            text = f"{pointer}{mark} {label}"

            if disabled:
                text += f" ({disabled})"

            lines.append((line_style, text + "\n"))

        lines.append(
            (
                "class:hint",
                "\n  >  current row    [x] selected    [ ] not selected"
                "    space: toggle    enter: confirm\n",
            )
        )

        return lines

    control = FormattedTextControl(_render, focusable=True)
    window = Window(content=control, dont_extend_height=True, wrap_lines=False)
    layout = Layout(HSplit([window]))

    style = Style.from_dict(
        {
            "question": "bold",
            "current": "reverse",
            "disabled": "fg:#888888 italic",
            "hint": "fg:#888888",
        }
    )

    app = Application(
        layout=layout,
        key_bindings=bindings,
        style=style,
        full_screen=False,
        erase_when_done=True,
    )

    return app.run()