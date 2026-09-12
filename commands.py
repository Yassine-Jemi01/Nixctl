from system_info import uses_flakes, flakes_name

import subprocess
import time


def clear_screen():
    subprocess.run(["clear"])


def wait_for_enter():
    input("\nPress Enter to continue...")
    clear_screen()


def authenticate_sudo():
    """Ask for the sudo password before starting the timer."""

    try:
        result = subprocess.run(
            ["sudo", "-v"],
            check=False,
        )

        return result.returncode == 0

    except KeyboardInterrupt:
        return False

    except Exception:
        return False


def run_command(command, use_sudo=False):
    process = None

    try:
        # Ask for sudo password BEFORE starting the timer.
        if use_sudo:
            if not authenticate_sudo():
                print("\n✗ Sudo authentication failed.")

                wait_for_enter()
                return False

        process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        start_time = time.time()

        while process.poll() is None:
            elapsed = int(time.time() - start_time)

            print(
                f"\r⏱ {elapsed}s",
                end="",
                flush=True,
            )

            time.sleep(1)

        elapsed = int(time.time() - start_time)

        if process.returncode == 0:
            print(f"\r✓ Success — {elapsed}s")
            success = True

        else:
            print(f"\r✗ Failed — {elapsed}s")
            success = False

        wait_for_enter()

        return success

    except KeyboardInterrupt:
        if process is not None and process.poll() is None:
            process.terminate()

        print("\n\n✗ Operation cancelled.")

        wait_for_enter()

        return False

    except Exception as error:
        print(f"\n✗ Unexpected error: {error}")

        wait_for_enter()

        return False


def rebuild():
    if uses_flakes():
        flake_name = flakes_name()

        if not flake_name:
            print("✗ Could not detect NixOS configuration name.")

            wait_for_enter()
            return False

        return run_command(
            [
                "sudo",
                "nixos-rebuild",
                "switch",
                "--flake",
                f"/etc/nixos#{flake_name}",
            ],
            use_sudo=True,
        )

    return run_command(
        [
            "sudo",
            "nixos-rebuild",
            "switch",
            "-I",
            "nixos-config=/etc/nixos/configuration.nix",
        ],
        use_sudo=True,
    )


def update():
    if uses_flakes():
        flake_name = flakes_name()

        if not flake_name:
            print("✗ Could not detect NixOS configuration name.")

            wait_for_enter()
            return False

        # Update the flake inputs (flake.lock) BEFORE rebuilding,
        # otherwise this behaves identically to rebuild() and never
        # actually pulls new package versions.
        if not run_command(
            [
                "nix",
                "flake",
                "update",
                "--flake",
                "/etc/nixos",
            ]
        ):
            return False

        return run_command(
            [
                "sudo",
                "nixos-rebuild",
                "switch",
                "--flake",
                f"/etc/nixos#{flake_name}",
            ],
            use_sudo=True,
        )

    return run_command(
        [
            "sudo",
            "nixos-rebuild",
            "switch",
            "--upgrade",
        ],
        use_sudo=True,
    )


def garbage_collect():
    if uses_flakes():
        return run_command(
            [
                "nix-collect-garbage",
                "--delete-old",
            ]
        )

    return run_command(
        [
            "nix-store",
            "--gc",
        ]
    )