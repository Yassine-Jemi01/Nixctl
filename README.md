# Nixctl

An interactive command-line tool for common NixOS system maintenance tasks. Nixctl provides a simple, menu-driven interface for rebuilding your configuration, updating your system, and cleaning up the Nix store, so you do not have to remember the exact `nixos-rebuild` and `nix` invocations for your specific setup.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [How It Works](#how-it-works)
- [Project Structure](#project-structure)
- [Notes and Caveats](#notes-and-caveats)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Overview

Nixctl is a Python-based command-line utility designed exclusively for NixOS. It detects whether your system uses a flake-based configuration or the legacy `configuration.nix` setup, then runs the correct commands automatically. This removes the need to memorize different command syntax for rebuilding, updating, or cleaning your system depending on how it is configured.

## Features

- **Rebuild**: Applies your current NixOS configuration using `nixos-rebuild switch`, automatically detecting whether you use a flake-based setup or the legacy `configuration.nix` setup.
- **Update**: Pulls in new package versions. On flake-based systems this runs `nix flake update` to refresh `flake.lock` before rebuilding. On legacy systems it runs `nixos-rebuild switch --upgrade`.
- **Garbage Collection**: Frees up disk space by removing old generations and unused store paths, using `nix-collect-garbage --delete-old` on flake-based systems or `nix-store --gc` on legacy systems.
- **Automatic Flake Detection**: Detects whether `/etc/nixos/flake.nix` exists and reads the flake's `nixosConfigurations` to determine the correct configuration name automatically.
- **Live Progress Feedback**: Displays an elapsed-time counter while a command runs and reports success or failure once it finishes.
- **Safe Sudo Handling**: Prompts for your sudo password up front, before starting any timed operation, so authentication delays are not counted as part of the command's runtime.
- **NixOS-Only Safeguard**: Checks `/etc/os-release` on startup and refuses to run on non-NixOS systems.

## Requirements

- NixOS
- Python 3.8 or newer
- [questionary](https://pypi.org/project/questionary/)

## Installation

Clone the repository and install the required Python dependency:

```bash
git clone https://github.com/Yassine-Jemi01/Nixctl.git
cd Nixctl
pip install -r requirements.txt
```

## Usage

Run the tool with:

```bash
python main.py
```

You will be presented with an interactive menu:

```
What do you want to do?
  Rebuild
  Update
  Garbage Collection
  Exit
```

Use the arrow keys to select an option and press Enter. Operations that require elevated privileges will prompt for your sudo password before starting.

## How It Works

Nixctl checks for the presence of `/etc/nixos/flake.nix` to decide which code path to take:

| Task               | Flake-Based System                                     | Legacy System                                                              |
|--------------------|----------------------------------------------------------|-----------------------------------------------------------------------------|
| Rebuild            | `sudo nixos-rebuild switch --flake /etc/nixos#<name>`     | `sudo nixos-rebuild switch -I nixos-config=/etc/nixos/configuration.nix`    |
| Update             | `nix flake update`, then rebuild using the flake          | `sudo nixos-rebuild switch --upgrade`                                       |
| Garbage Collection | `nix-collect-garbage --delete-old`                        | `nix-store --gc`                                                             |

When flakes are used, the configuration name is read directly from the output of `nix flake show --json /etc/nixos`, so it never needs to be hardcoded.

## Project Structure

```
.
├── main.py              # Entry point, NixOS check, and interactive menu
├── commands.py          # Command execution, sudo handling, and rebuild/update/gc logic
├── system_info.py       # Flake detection and configuration name lookup
├── requirements.txt     # Python dependencies
├── LICENSE              # MIT License
└── README.md            # Project documentation
```

## Notes and Caveats

- Running `Update` on a flake-based system updates all flake inputs at once. For granular control over individual inputs, run `nix flake update <input-name>` manually instead.
- Because NixOS retains previous generations, a failed or unwanted update can be rolled back from the boot menu or with `sudo nixos-rebuild switch --rollback`.
- Writing to `/etc/nixos/flake.lock` requires write permission on that file or directory. If the update step fails immediately, check the ownership and permissions of `/etc/nixos`.

## Troubleshooting

- **The tool refuses to start**: Nixctl checks `/etc/os-release` and only runs on NixOS. Confirm you are running it on a NixOS system.
- **Sudo prompt does not appear or hangs**: Ensure your user has sudo privileges configured correctly and that no other process is holding a lock on the Nix store.
- **Update fails immediately on a flake-based system**: Check that you have write permission to `/etc/nixos/flake.lock` and its containing directory.
- **Configuration name not detected**: Verify that `/etc/nixos/flake.nix` defines a valid `nixosConfigurations` output that `nix flake show --json` can read.

## Contributing

Issues and pull requests are welcome. If you are adding a new command, follow the same pattern used by `rebuild()`, `update()`, and `garbage_collect()`:

1. Branch the logic on `uses_flakes()` to determine flake versus legacy behavior.
2. Build the appropriate command list for each case.
3. Pass the resulting command to `run_command()` for execution and progress reporting.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
