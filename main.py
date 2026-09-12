import questionary

from commands import rebuild, update, garbage_collect


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


def show_menu():
    while True:
        try:
            choice = questionary.select(
                "What do you want to do?",
                choices=[
                    "Rebuild",
                    "Update",
                    "Garbage Collection",
                    "Exit",
                ],
            ).ask()

            if choice == "Rebuild":
                rebuild()

            elif choice == "Update":
                update()

            elif choice == "Garbage Collection":
                garbage_collect()

            elif choice == "Exit" or choice is None:
                print("Goodbye!")
                break

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