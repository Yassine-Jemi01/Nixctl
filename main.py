from commands import (
    garbage_collect,
    list_generations,
    rebuild,
    search_package,
    update,
    validate_config,
)
from system_info import is_nixos
from ui import multi_select


VERSION = "0.1.0"


def print_nixos_banner() -> None:
    banner = r"""
 __   __     ______     __         __
/\ "-.\ \   /\  ___\   /\ \       /\ \
\ \ \-.  \  \ \ \____  \ \ \____  \ \ \
 \ \_\\"\_\  \ \_____\  \ \_____\  \ \_\
  \/_/ \/_/   \/_____/   \/_____/   \/_/
"""

    print(
        "\033[38;2;126;186;228m"
        + banner
        + "\033[0m"
    )

    print("NixOS CLI Tool")
    print(f"v{VERSION}\n")


ACTIONS = [
    ("validate", "Validate Config", validate_config),
    ("rebuild", "Rebuild", rebuild),
    ("update", "Update", update),
    ("gc", "Garbage Collection", garbage_collect),
    ("list_gen", "List Generations", list_generations),
    ("search", "Search Package", search_package),
]


def show_menu() -> None:
    """Run the main interactive menu."""
    while True:
        try:
            options = [
                (label, key, None)
                for key, label, _ in ACTIONS
            ]

            selected = multi_select(
                "What do you want to do?",
                options,
            )

            if selected is None or not selected:
                print("Goodbye!")
                return

            for key, _, action in ACTIONS:
                if key in selected:
                    action()

        except KeyboardInterrupt:
            print("\nGoodbye!")
            return

        except Exception as error:
            print(f"\nUnexpected error: {error}")


def main() -> None:
    if not is_nixos():
        print(
            "\033[38;2;255;0;0m"
            "This is a NixOS-only tool"
            "\033[0m"
        )
        return

    print_nixos_banner()
    show_menu()


if __name__ == "__main__":
    main()