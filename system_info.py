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