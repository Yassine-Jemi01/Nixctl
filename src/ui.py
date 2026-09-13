from prompt_toolkit import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import HSplit, Layout, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.styles import Style


Option = tuple[str, object, str | None]


def multi_select(
    message: str,
    options: list[Option],
) -> list[object] | None:
    """Display a simple interactive multi-select menu."""
    if not options:
        return []

    selected: set[object] = set()
    cursor = 0
    count = len(options)

    bindings = KeyBindings()

    @bindings.add("up")
    def _move_up(event) -> None:
        nonlocal cursor
        cursor = (cursor - 1) % count

    @bindings.add("down")
    def _move_down(event) -> None:
        nonlocal cursor
        cursor = (cursor + 1) % count

    @bindings.add(" ")
    def _toggle(event) -> None:
        _, value, disabled = options[cursor]

        if disabled:
            return

        if value in selected:
            selected.remove(value)
        else:
            selected.add(value)

    @bindings.add("enter")
    def _confirm(event) -> None:
        values = [
            value
            for _, value, disabled in options
            if value in selected and not disabled
        ]

        event.app.exit(result=values)

    @bindings.add("c-c")
    @bindings.add("escape")
    def _cancel(event) -> None:
        event.app.exit(result=None)

    def _render():
        lines = [
            (
                "class:question",
                f"? {message}\n",
            )
        ]

        for index, (
            label,
            value,
            disabled,
        ) in enumerate(options):
            pointer = "> " if index == cursor else "  "
            mark = (
                "[x]"
                if value in selected
                else "[ ]"
            )

            line_style = ""

            if disabled:
                line_style = "class:disabled"
            elif index == cursor:
                line_style = "class:current"

            text = f"{pointer}{mark} {label}"

            if disabled:
                text += f" ({disabled})"

            lines.append(
                (
                    line_style,
                    text + "\n",
                )
            )

        lines.append(
            (
                "class:hint",
                "\n"
                "  ↑/↓ move    [x] selected"
                "    [ ] not selected\n"
                "  space: toggle    enter: confirm"
                "    esc: cancel\n",
            )
        )

        return lines

    control = FormattedTextControl(
        _render,
        focusable=True,
    )

    window = Window(
        content=control,
        dont_extend_height=True,
        wrap_lines=False,
    )

    layout = Layout(
        HSplit([window])
    )

    style = Style.from_dict(
        {
            "question": "bold",
            "current": "reverse",
            "disabled": "fg:#888888 italic",
            "hint": "fg:#888888",
        }
    )

    application = Application(
        layout=layout,
        key_bindings=bindings,
        style=style,
        full_screen=False,
        erase_when_done=True,
    )

    return application.run()