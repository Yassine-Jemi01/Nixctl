from system_info import uses_flakes, flakes_name, get_generations, search_packages

import subprocess
import time
import questionary


def clear_screen():
    subprocess.run(["clear"])


def wait_for_enter():
    input("\nPress Enter to continue...")
    clear_screen()


def authenticate_sudo():
    """Ask for the sudo password up front, before anything else runs."""

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
    """Run a command with a live elapsed-time counter, discarding output."""

    process = None

    try:
        if use_sudo:
            if not authenticate_sudo():
                print("\n✗ Sudo authentication failed.")
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
            return True

        print(f"\r✗ Failed — {elapsed}s")
        return False

    except KeyboardInterrupt:
        if process is not None and process.poll() is None:
            process.terminate()

        print("\n\n✗ Operation cancelled.")
        return False

    except Exception as error:
        print(f"\n✗ Unexpected error: {error}")
        return False


def run_and_capture(command):
    """Run a quick command and capture its output (no live timer).

    Used for informational commands: diffing, searching, validating.
    """

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )

        return result.returncode == 0, result.stdout, result.stderr

    except Exception as error:
        return False, "", str(error)


def _flake_target():
    flake_name = flakes_name()

    if not flake_name:
        print("✗ Could not detect NixOS configuration name.")
        return None

    return f"/etc/nixos#{flake_name}"


def _build_new_system(extra_args=None):
    """Build the new system into ./result without activating it."""

    extra_args = extra_args or []

    if uses_flakes():
        target = _flake_target()

        if not target:
            return False

        return run_command(
            ["sudo", "nixos-rebuild", "build", "--flake", target, *extra_args],
            use_sudo=True,
        )

    return run_command(
        [
            "sudo",
            "nixos-rebuild",
            "build",
            "-I",
            "nixos-config=/etc/nixos/configuration.nix",
            *extra_args,
        ],
        use_sudo=True,
    )


def _show_diff():
    """Show what would change compared to the currently running system."""

    print("\nComparing with the currently running system...\n")

    success, stdout, stderr = run_and_capture(
        [
            "nix",
            "store",
            "diff-closures",
            "/run/current-system",
            "./result",
        ]
    )

    if not success:
        print("(Could not compute a diff — this needs the 'nix-command'")
        print(" experimental feature enabled in your Nix settings.)")
        return

    if stdout.strip():
        print(stdout)
    else:
        print("No visible package differences.")


def _apply_new_system(mode):
    """Activate the already-built system with 'switch' or 'boot'."""

    if uses_flakes():
        target = _flake_target()

        if not target:
            return False

        return run_command(
            ["sudo", "nixos-rebuild", mode, "--flake", target],
            use_sudo=True,
        )

    return run_command(
        [
            "sudo",
            "nixos-rebuild",
            mode,
            "-I",
            "nixos-config=/etc/nixos/configuration.nix",
        ],
        use_sudo=True,
    )


def _cleanup_result_link():
    subprocess.run(["rm", "-f", "./result"])


def _confirm_and_apply():
    """Shared flow: show the diff, confirm, choose switch/boot, apply."""

    _show_diff()

    proceed = questionary.confirm("\nApply this change to your system?").ask()

    if not proceed:
        print("Cancelled — nothing was applied.")
        _cleanup_result_link()
        wait_for_enter()
        return False

    mode = questionary.select(
        "When should it take effect?",
        choices=[
            questionary.Choice("Switch now", value="switch"),
            questionary.Choice("On next boot", value="boot"),
        ],
    ).ask()

    if mode is None:
        mode = "switch"

    success = _apply_new_system(mode)

    _cleanup_result_link()
    wait_for_enter()

    return success


def rebuild():
    # Ask for the sudo password before doing anything else, so the
    # user isn't surprised by a password prompt partway through.
    if not authenticate_sudo():
        print("✗ Sudo authentication failed.")
        wait_for_enter()
        return False

    if not _build_new_system():
        wait_for_enter()
        return False

    return _confirm_and_apply()


def update():
    if not authenticate_sudo():
        print("✗ Sudo authentication failed.")
        wait_for_enter()
        return False

    if uses_flakes():
        flake_name = flakes_name()

        if not flake_name:
            print("✗ Could not detect NixOS configuration name.")
            wait_for_enter()
            return False

        # Update flake.lock BEFORE building, otherwise this behaves
        # identically to rebuild() and never pulls in new versions.
        if not run_command(["nix", "flake", "update", "--flake", "/etc/nixos"]):
            print("✗ Could not update flake.lock. Check write permissions")
            print("  on /etc/nixos, then try again.")
            wait_for_enter()
            return False

        if not _build_new_system():
            wait_for_enter()
            return False

        return _confirm_and_apply()

    if not _build_new_system(extra_args=["--upgrade"]):
        wait_for_enter()
        return False

    return _confirm_and_apply()


def garbage_collect():
    if uses_flakes():
        result = run_command(["nix-collect-garbage", "--delete-old"])
    else:
        result = run_command(["nix-store", "--gc"])

    wait_for_enter()
    return result


def list_generations():
    print("Fetching generations...\n")

    generations = get_generations()

    if not generations:
        print("✗ Could not read generations, or none were found.")
        wait_for_enter()
        return False

    choices = [
        questionary.Choice(
            f"{gen['id']} — {gen['date']}" + (" (current)" if gen["current"] else ""),
            value=gen["id"],
            disabled="current generation" if gen["current"] else None,
        )
        for gen in generations
    ]

    to_delete = questionary.checkbox(
        "Select generations to delete (space to select, enter to confirm):",
        choices=choices,
    ).ask()

    if not to_delete:
        print("No generations selected. Nothing deleted.")
        wait_for_enter()
        return False

    confirm = questionary.confirm(
        f"Delete {len(to_delete)} generation(s)? This cannot be undone."
    ).ask()

    if not confirm:
        print("Cancelled.")
        wait_for_enter()
        return False

    if not authenticate_sudo():
        print("✗ Sudo authentication failed.")
        wait_for_enter()
        return False

    success = run_command(
        [
            "sudo",
            "nix-env",
            "--delete-generations",
            *[str(i) for i in to_delete],
            "-p",
            "/nix/var/nix/profiles/system",
        ],
        use_sudo=True,
    )

    if success:
        print("Run Garbage Collection to reclaim the freed disk space.")

    wait_for_enter()
    return success


def search_package():
    query = questionary.text("Search for a package:").ask()

    if not query:
        return False

    print(f"\nSearching for '{query}'... (this can take a while the first time)\n")

    results = search_packages(query)

    if results is None:
        print("✗ Search failed. Make sure the 'nix-command' experimental")
        print("  feature is enabled.")
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
        print(f"\n...and {len(results) - 25} more results.")

    wait_for_enter()
    return True


def validate_config():
    print("Validating configuration...\n")

    if uses_flakes():
        success, stdout, stderr = run_and_capture(
            ["nix", "flake", "check", "/etc/nixos"]
        )
    else:
        success, stdout, stderr = run_and_capture(
            [
                "nixos-rebuild",
                "dry-build",
                "-I",
                "nixos-config=/etc/nixos/configuration.nix",
            ]
        )

    if success:
        print("✓ Configuration looks valid.")
    else:
        print("✗ Configuration has errors:\n")
        print(stderr or stdout)

    wait_for_enter()
    return success