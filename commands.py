import os
import shutil
import subprocess
import time
from typing import Sequence

import questionary

from system_info import (
    NIXOS_CONFIG_DIR,
    SYSTEM_PROFILE,
    flakes_name,
    get_generations,
    search_packages,
    uses_flakes,
)
from ui import multi_select


RESULT_LINK = f"/tmp/nixctl-result-{os.getpid()}"


def clear_screen() -> None:
    """Clear the terminal screen."""
    subprocess.run(
        ["clear"],
        check=False,
    )


def wait_for_enter() -> None:
    """Wait for the user, then clear the screen."""
    input("\nPress Enter to continue...")
    clear_screen()


def authenticate_sudo() -> bool:
    """Authenticate sudo before a privileged operation."""
    try:
        result = subprocess.run(
            ["sudo", "-v"],
            check=False,
        )

        return result.returncode == 0

    except KeyboardInterrupt:
        return False

    except OSError:
        return False


def _cleanup_result_link() -> None:
    """Remove the temporary nixos-rebuild result link."""
    try:
        os.remove(RESULT_LINK)
    except FileNotFoundError:
        pass


def run_command(
    command: Sequence[str],
    use_sudo: bool = False,
) -> bool:
    """
    Run a long-running command with an elapsed-time counter.

    Command output is intentionally hidden to keep the interface clean.
    """
    process: subprocess.Popen | None = None

    try:
        if use_sudo and not authenticate_sudo():
            print("\n✗ Sudo authentication failed.")
            return False

        process = subprocess.Popen(
            list(command),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        start_time = time.monotonic()

        while process.poll() is None:
            elapsed = int(time.monotonic() - start_time)

            print(
                f"\r⏱ {elapsed}s",
                end="",
                flush=True,
            )

            time.sleep(0.2)

        elapsed = int(time.monotonic() - start_time)

        if process.returncode == 0:
            print(f"\r✓ Success — {elapsed}s")
            return True

        print(f"\r✗ Failed — {elapsed}s")
        return False

    except KeyboardInterrupt:
        if process is not None and process.poll() is None:
            process.terminate()

            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()

        print("\n\n✗ Operation cancelled.")
        return False

    except OSError as error:
        print(f"\n✗ Could not start command: {error}")
        return False

    except Exception as error:
        print(f"\n✗ Unexpected error: {error}")
        return False


def run_and_capture(
    command: Sequence[str],
) -> tuple[bool, str, str]:
    """Run a short command and return success, stdout, and stderr."""
    try:
        result = subprocess.run(
            list(command),
            capture_output=True,
            text=True,
            check=False,
        )

        return (
            result.returncode == 0,
            result.stdout,
            result.stderr,
        )

    except OSError as error:
        return False, "", str(error)


def _flake_target() -> str | None:
    """Build the /etc/nixos flake target automatically."""
    flake_name = flakes_name()

    if not flake_name:
        print("✗ Could not detect NixOS configuration name.")
        return None

    return f"{NIXOS_CONFIG_DIR}#{flake_name}"


def _build_new_system(extra_args: Sequence[str] | None = None) -> bool:
    """Build the next system generation without activating it."""
    extra_args = list(extra_args or [])

    _cleanup_result_link()

    if uses_flakes():
        target = _flake_target()

        if not target:
            return False

        command = [
            "sudo",
            "nixos-rebuild",
            "build",
            "--flake",
            target,
            "--out-link",
            RESULT_LINK,
            *extra_args,
        ]

    else:
        command = [
            "sudo",
            "nixos-rebuild",
            "build",
            "--out-link",
            RESULT_LINK,
            "-I",
            f"nixos-config={NIXOS_CONFIG_DIR}/configuration.nix",
            *extra_args,
        ]

    return run_command(
        command,
        use_sudo=True,
    )


def _show_diff() -> None:
    """Show the closure difference between running and built systems."""
    print("\nComparing with the currently running system...\n")

    success, stdout, stderr = run_and_capture(
        [
            "nix",
            "store",
            "diff-closures",
            "/run/current-system",
            RESULT_LINK,
        ]
    )

    if not success:
        print("Could not compute a system diff.")
        if stderr.strip():
            print(f"\n{stderr.strip()}")

        return

    output = stdout.strip()

    if output:
        print(output)
    else:
        print("No visible package differences.")


def _apply_new_system(mode: str) -> bool:
    """Activate the built configuration."""
    if mode not in {"switch", "boot"}:
        return False

    if uses_flakes():
        target = _flake_target()

        if not target:
            return False

        command = [
            "sudo",
            "nixos-rebuild",
            mode,
            "--flake",
            target,
        ]

    else:
        command = [
            "sudo",
            "nixos-rebuild",
            mode,
            "-I",
            f"nixos-config={NIXOS_CONFIG_DIR}/configuration.nix",
        ]

    return run_command(
        command,
        use_sudo=True,
    )


def _confirm_and_apply() -> bool:
    """Show the diff, confirm it, then switch or boot."""
    _show_diff()

    proceed = questionary.confirm(
        "\nApply this change to your system?"
    ).ask()

    if not proceed:
        print("Cancelled — nothing was applied.")
        _cleanup_result_link()
        wait_for_enter()
        return False

    mode = questionary.select(
        "When should it take effect?",
        choices=[
            questionary.Choice(
                "Switch now",
                value="switch",
            ),
            questionary.Choice(
                "On next boot",
                value="boot",
            ),
        ],
    ).ask()

    if mode is None:
        mode = "switch"

    success = _apply_new_system(mode)

    _cleanup_result_link()
    wait_for_enter()

    return success


def rebuild() -> bool:
    """Build and optionally activate the current configuration."""
    if not authenticate_sudo():
        print("✗ Sudo authentication failed.")
        wait_for_enter()
        return False

    if not _build_new_system():
        wait_for_enter()
        return False

    return _confirm_and_apply()


def update() -> bool:
    """Update flake inputs or legacy channels, then rebuild."""
    if not authenticate_sudo():
        print("✗ Sudo authentication failed.")
        wait_for_enter()
        return False

    if uses_flakes():
        if not flakes_name():
            print("✗ Could not detect NixOS configuration name.")
            wait_for_enter()
            return False

        updated = run_command(
            [
                "sudo",
                "nix",
                "flake",
                "update",
                "--flake",
                NIXOS_CONFIG_DIR,
            ],
            use_sudo=True,
        )

        if not updated:
            print("✗ Could not update flake.lock.")
            wait_for_enter()
            return False

    else:
        if not _build_new_system(extra_args=["--upgrade"]):
            wait_for_enter()
            return False

        return _confirm_and_apply()

    if not _build_new_system():
        wait_for_enter()
        return False

    return _confirm_and_apply()


def garbage_collect() -> bool:
    """Remove old Nix generations/store paths."""
    if uses_flakes():
        command = [
            "sudo",
            "nix-collect-garbage",
            "--delete-old",
        ]
    else:
        command = [
            "sudo",
            "nix-store",
            "--gc",
        ]

    success = run_command(
        command,
        use_sudo=True,
    )

    wait_for_enter()

    return success


def list_generations() -> bool:
    """Show system generations and delete selected ones."""
    print("Fetching generations...\n")

    if not authenticate_sudo():
        print("✗ Sudo authentication failed.")
        wait_for_enter()
        return False

    generations, error = get_generations()

    if error:
        print("✗ Could not read system generations.")
        print(f"\n{error}")
        wait_for_enter()
        return False

    if not generations:
        print("No system generations were found.")
        wait_for_enter()
        return False

    options = [
        (
            f"{generation['id']} — {generation['date']}"
            + (
                " (current)"
                if generation["current"]
                else ""
            ),
            generation["id"],
            (
                "current generation"
                if generation["current"]
                else None
            ),
        )
        for generation in generations
    ]

    selected = multi_select(
        "Select generations to delete",
        options,
    )

    if selected is None or not selected:
        print("No generations selected. Nothing deleted.")
        wait_for_enter()
        return False

    current_ids = {
        generation["id"]
        for generation in generations
        if generation["current"]
    }

    selected_ids = [
        generation_id
        for generation_id in selected
        if generation_id not in current_ids
    ]

    if not selected_ids:
        print("✗ The current generation cannot be deleted.")
        wait_for_enter()
        return False

    if len(selected_ids) != len(selected):
        print("Current generation was automatically excluded.")

    confirm = questionary.confirm(
        f"\nDelete {len(selected_ids)} generation(s)? "
        "This cannot be undone."
    ).ask()

    if not confirm:
        print("Cancelled.")
        wait_for_enter()
        return False

    success = run_command(
        [
            "sudo",
            "nix-env",
            "--delete-generations",
            *[str(generation_id) for generation_id in selected_ids],
            "--profile",
            SYSTEM_PROFILE,
        ],
        use_sudo=True,
    )

    if success:
        print(
            "\nRun Garbage Collection to reclaim "
            "the freed disk space."
        )

    wait_for_enter()

    return success


def search_package() -> bool:
    """Search nixpkgs for a package."""
    query = questionary.text(
        "Search for a package:"
    ).ask()

    if not query:
        return False

    query = query.strip()

    if not query:
        return False

    print(
        f"\nSearching for '{query}'..."
        " (this can take a while the first time)\n"
    )

    results = search_packages(query)

    if results is None:
        print("✗ Search failed.")
        print(
            "Make sure the 'nix-command' experimental "
            "feature is enabled."
        )
        wait_for_enter()
        return False

    if not results:
        print("No packages found.")
        wait_for_enter()
        return False

    for attr, info in list(results.items())[:25]:
        name = info.get("pname", attr)
        version = info.get("version", "")
        description = info.get("description", "")

        print(f"  {name} {version}")

        if description:
            print(f"    {description}")

    if len(results) > 25:
        print(
            f"\n...and {len(results) - 25} more results."
        )

    wait_for_enter()

    return True


def validate_config() -> bool:
    """Validate the current NixOS configuration."""
    print("Validating configuration...\n")

    if uses_flakes():
        command = [
            "nix",
            "flake",
            "check",
            NIXOS_CONFIG_DIR,
        ]
    else:
        command = [
            "nixos-rebuild",
            "dry-build",
            "-I",
            f"nixos-config={NIXOS_CONFIG_DIR}/configuration.nix",
        ]

    success, stdout, stderr = run_and_capture(command)

    if success:
        print("✓ Configuration looks valid.")
    else:
        print("✗ Configuration has errors:\n")
        print(stderr.strip() or stdout.strip())

    wait_for_enter()

    return success