from commands import (
    rebuild,
    update,
    garbage_collect,
    list_generations,
    search_package,
    validate_config,
)
from ui import multi_select


def is_nixos():
    try:
        with open("/etc/os-release", "r", encoding="utf-8") as file:
            return any(
                line.strip() == "ID=nixos"
                for line in file
            )

    except FileNotFoundError:
        return False

    except PermissionError:
        print("Error: Permission denied.")
        return False


def print_nixos_banner():
    banner = r"""
 __   __     ______     __         __
/\ "-.\ \   /\  ___\   /\ \       /\ \
\ \ \-.  \  \ \ \____  \ \ \____  \ \ \
 \ \_\\"\_\  \ \_____\  \ \_____\  \ \_\
  \/_/ \/_/   \/_____/   \/_____/   \/_/
"""

    print("\033[38;2;126;186;228m" + banner + "\033[0m")
    print("NixOS CLI Tool")
    print("v0.1.0\n")


# Order matters: this is the sequence actions run in when several are
# selected at once. Validation runs first so a broken config is caught
# before spending time on a build.
ACTIONS = [
    ("validate", "Validate Config", validate_config),
    ("rebuild", "Rebuild", rebuild),
    ("update", "Update", update),
    ("gc", "Garbage Collection", garbage_collect),
    ("list_gen", "List Generations", list_generations),
    ("search", "Search Package", search_package),
]


def show_menu():
    while True:
        try:
            options = [(label, key, None) for key, label, _ in ACTIONS]

            selected = multi_select("What do you want to do?", options)

            if not selected:
                print("Goodbye!")
                break

            for key, _, action in ACTIONS:
                if key in selected:
                    action()

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break

        except Exception as error:
            print(f"\nUnexpected error: {error}")


def main():
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