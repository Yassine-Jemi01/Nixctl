import json
import os
import socket
import subprocess


def get_hostname():
    return socket.gethostname()


def uses_flakes():
    return os.path.isfile("/etc/nixos/flake.nix")


def flakes_name():
    if not uses_flakes():
        return None

    try:
        result = subprocess.run(
            [
                "nix",
                "flake",
                "show",
                "--json",
                "/etc/nixos",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        data = json.loads(result.stdout)

        configurations = data.get(
            "nixosConfigurations",
            {},
        )

        if not configurations:
            return None

        return next(iter(configurations))

    except (
        subprocess.CalledProcessError,
        json.JSONDecodeError,
    ):
        return None


def get_generations():
    """Return a list of {id, date, current} dicts for the system profile."""

    try:
        result = subprocess.run(
            [
                "nix-env",
                "--list-generations",
                "-p",
                "/nix/var/nix/profiles/system",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

    except (subprocess.CalledProcessError, FileNotFoundError):
        return []

    generations = []

    for line in result.stdout.splitlines():
        line = line.strip()

        if not line:
            continue

        parts = line.split()

        if len(parts) < 3:
            continue

        try:
            gen_id = int(parts[0])
        except ValueError:
            continue

        date = f"{parts[1]} {parts[2]}"
        current = "current" in line

        generations.append(
            {
                "id": gen_id,
                "date": date,
                "current": current,
            }
        )

    return generations


def search_packages(query):
    """Search nixpkgs for a package. Returns a dict of results, or None on error."""

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

    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None