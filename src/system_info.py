import json
import os
import socket
import subprocess
from typing import Any


NIXOS_CONFIG_DIR = "/etc/nixos"
SYSTEM_PROFILE = "/nix/var/nix/profiles/system"


def get_hostname() -> str:
    """Return the current machine hostname."""
    return socket.gethostname()


def is_nixos() -> bool:
    """Return True when the current operating system is NixOS."""
    try:
        with open("/etc/os-release", "r", encoding="utf-8") as file:
            for line in file:
                if line.strip() == "ID=nixos":
                    return True

    except (FileNotFoundError, PermissionError):
        pass

    return False


def uses_flakes() -> bool:
    """Return True when the NixOS configuration uses a flake."""
    return os.path.isfile(
        os.path.join(NIXOS_CONFIG_DIR, "flake.nix")
    )


def flakes_name() -> str | None:
    """Detect the first nixosConfiguration name from the system flake."""
    if not uses_flakes():
        return None

    try:
        result = subprocess.run(
            [
                "nix",
                "flake",
                "show",
                "--json",
                NIXOS_CONFIG_DIR,
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        data: dict[str, Any] = json.loads(result.stdout)
        configurations = data.get("nixosConfigurations", {})

        if not configurations:
            return None

        return next(iter(configurations))

    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
        json.JSONDecodeError,
    ):
        return None


def get_generations() -> tuple[list[dict[str, Any]], str | None]:
    """
    Return system generations.

    Each generation contains:
        id: int
        date: str
        current: bool

    The second return value contains an error message when the command fails.
    """
    if not os.path.exists(SYSTEM_PROFILE):
        return [], f"System profile not found: {SYSTEM_PROFILE}"

    try:
        result = subprocess.run(
            [
                "sudo",
                "nix-env",
                "--profile",
                SYSTEM_PROFILE,
                "--list-generations",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    except FileNotFoundError as error:
        return [], str(error)

    if result.returncode != 0:
        error = result.stderr.strip()

        if not error:
            error = "nix-env failed to list system generations."

        return [], error

    generations: list[dict[str, Any]] = []

    for line in result.stdout.splitlines():
        line = line.strip()

        if not line:
            continue

        parts = line.split()

        if len(parts) < 3:
            continue

        try:
            generation_id = int(parts[0])
        except ValueError:
            continue

        date = f"{parts[1]} {parts[2]}"
        current = "(current)" in line

        generations.append(
            {
                "id": generation_id,
                "date": date,
                "current": current,
            }
        )

    return generations, None


def search_packages(query: str) -> dict[str, Any] | None:
    """Search nixpkgs for a package."""
    try:
        result = subprocess.run(
            [
                "nix",
                "search",
                "nixpkgs",
                query,
                "--json",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        return json.loads(result.stdout)

    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
        json.JSONDecodeError,
    ):
        return None