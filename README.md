# Nixctl

An interactive command-line tool for common NixOS system maintenance tasks. Nixctl provides a menu-driven interface for validating, rebuilding, and updating your configuration, cleaning up the Nix store, listing generations, and searching packages, so you do not have to remember the exact `nixos-rebuild` and `nix` invocations for your specific setup.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
  - [Run Without Installing (Flake)](#run-without-installing-flake)
  - [Install Into Your Profile (Flake)](#install-into-your-profile-flake)
  - [Add as a Flake Input to Your System](#add-as-a-flake-input-to-your-system)
  - [Manual Installation (Clone and Run)](#manual-installation-clone-and-run)
- [Usage](#usage)
- [Updating](#updating)
  - [Updating a Profile Install](#updating-a-profile-install)
  - [Updating a Manual Clone](#updating-a-manual-clone)
- [How It Works](#how-it-works)
  - [Flake vs Legacy Detection](#flake-vs-legacy-detection)
  - [Build, Diff, Confirm](#build-diff-confirm)
- [Project Structure](#project-structure)
- [Notes and Caveats](#notes-and-caveats)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Overview

Nixctl is a Python-based command-line utility designed exclusively for NixOS. It detects whether your system uses a flake-based configuration or the legacy `configuration.nix` setup, then runs the correct commands automatically. Before applying any change, it builds the new system, shows you a diff against what is currently running, and waits for your confirmation, so nothing is activated blindly.

## Features

- **Validate Config** — Checks your configuration for errors using `nix flake check` or `nixos-rebuild dry-build` before you commit to a full rebuild.
- **Rebuild** — Applies your current NixOS configuration with `nixos-rebuild switch`, automatically detecting whether you use a flake-based setup or the legacy `configuration.nix` setup.
- **Update** — Pulls in new package versions. On flake-based systems this runs `nix flake update` to refresh `flake.lock` before rebuilding; on legacy systems it runs `nixos-rebuild switch --upgrade`.
- **Garbage Collection** — Frees up disk space by removing old generations and unused store paths, using `nix-collect-garbage --delete-old` (flakes) or `nix-store --gc` (legacy).
- **List Generations** — Shows the available NixOS system generations so you can see what is currently installed and what can be rolled back to.
- **Search Package** — Looks up a package by name so you can check availability before adding it to your configuration.
- **Diff before applying** — Every rebuild or update builds the new system into `./result` first, then shows a `nix store diff-closures` comparison against the currently running system (`/run/current-system`) before anything is activated. The `./result` symlink is removed automatically once the operation finishes.
- **Switch or boot** — Choose whether a change takes effect immediately or only on the next reboot.
- **Multi-select menu** — Select multiple actions at once with the spacebar (for example, validate, then update, then collect garbage, in a single pass) and confirm with Enter. This is a minimal custom selector (see `ui.py`): Space is the only way to toggle a selection, with no "select all" or "invert selection" shortcut, so nothing gets picked by accident.
- **Automatic flake detection** — Detects `/etc/nixos/flake.nix` and reads the flake's `nixosConfigurations` to determine the configuration name automatically, with no hardcoding required.
- **Live progress feedback** — Shows an elapsed-time counter while a command runs and reports success or failure when it finishes.
- **Safe sudo handling** — Prompts for your sudo password up front, before starting any timed operation, so authentication delays are not counted as part of the command's runtime.
- **NixOS-only safeguard** — Checks `/etc/os-release` on startup and refuses to run on non-NixOS systems.

## Requirements

- NixOS
- Python 3.8 or newer
- [questionary](https://pypi.org/project/questionary/)
- Nix with flakes enabled, if you want to run or install Nixctl as a flake

## Installation

Nixctl can be run directly from its flake without installing anything, installed into your Nix profile, added as an input to your own system flake, or cloned and run manually with Python. Pick whichever fits your workflow.

### Run Without Installing (Flake)

If you just want to try Nixctl once, run it straight from GitHub:

```bash
nix run github:Yassine-Jemi01/Nixctl
```

This fetches the flake, builds it, and launches the interactive menu without leaving anything installed on your system afterward.

### Install Into Your Profile (Flake)

To have Nixctl available as a regular command on your system, add it to your Nix profile:

```bash
nix profile add github:Yassine-Jemi01/Nixctl
```

Do not pin the install to a specific commit (for example `github:Yassine-Jemi01/Nixctl/<commit-hash>`), since that locks you to that exact commit forever and `nix profile upgrade` will not move past it. Using the plain URL above always resolves to the latest `main` at install time and lets `nix profile upgrade` pull in newer commits later.

### Add as a Flake Input to Your System

You can also add Nixctl as an input to your own system flake and include its package in `environment.systemPackages`:

```nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    nixctl.url = "github:Yassine-Jemi01/Nixctl";
  };

  outputs = { self, nixpkgs, nixctl, ... }: {
    nixosConfigurations.myhost = nixpkgs.lib.nixosSystem {
      system = "x86_64-linux";
      modules = [
        {
          environment.systemPackages = [
            nixctl.packages.x86_64-linux.default
          ];
        }
        # your other modules
      ];
    };
  };
}
```

Rebuilding your system afterward makes the `nixctl` command available to every user on the machine.

### Manual Installation (Clone and Run)

If you would rather manage the Python dependency yourself, clone the repository directly:

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

Or, if installed via `nix profile add` or as a system package:

```bash
nixctl
```

You will be presented with a multi-select menu:

```
? What do you want to do?
> [ ] Validate Config
  [ ] Rebuild
  [ ] Update
  [ ] Garbage Collection
  [ ] List Generations
  [ ] Search Package
> current row   [x] selected   [ ] not selected
space: toggle   enter: confirm
```

Use the arrow keys to move between options, Space to select one or more actions, and Enter to run them. Operations that require elevated privileges will prompt for your sudo password before starting. When a rebuild or update is selected, Nixctl builds the new system, shows you what would change, and asks you to confirm before switching or booting into it.

## Updating

### Updating a Profile Install

If you installed Nixctl with `nix profile add`, it will not pick up new versions on its own. Once new commits are pushed to `main`, refresh it explicitly:

```bash
nix profile list
nix profile upgrade Nixctl --refresh
```

Nix names the profile entry after the flake's repository, so the name is case-sensitive. Check the exact name (and index) with `nix profile list` first; if `upgrade Nixctl` does not match, use the index shown instead, for example `nix profile upgrade 3 --refresh`. The `--refresh` flag is required: without it, Nix reuses its local evaluation cache instead of checking GitHub for new commits, and the upgrade will silently do nothing.

### Updating a Manual Clone

If you cloned the repository manually, update it with:

```bash
cd Nixctl
git pull
pip install -r requirements.txt --upgrade
```

## How It Works

### Flake vs Legacy Detection

Nixctl checks for the presence of `/etc/nixos/flake.nix` to decide which code path to take:

| Task               | Flake-Based System                                      | Legacy System                                                              |
|--------------------|-------------------------------------------------------------|-----------------------------------------------------------------------------|
| Validate Config    | `nix flake check`                                            | `nixos-rebuild dry-build`                                                    |
| Rebuild            | `sudo nixos-rebuild switch --flake /etc/nixos#<name>`        | `sudo nixos-rebuild switch -I nixos-config=/etc/nixos/configuration.nix`     |
| Update             | `nix flake update`, then rebuild using the flake              | `sudo nixos-rebuild switch --upgrade`                                        |
| Garbage Collection | `nix-collect-garbage --delete-old`                            | `nix-store --gc`                                                             |

When flakes are used, the configuration name is read directly from the output of `nix flake show --json /etc/nixos`, so it never needs to be hardcoded.

### Build, Diff, Confirm

Rebuild and Update never activate a new system blindly. Nixctl:

1. Builds the new system into `./result` without switching to it.
2. Compares it against the currently running system with `nix store diff-closures /run/current-system ./result`, so you can see exactly what packages and versions would change.
3. Asks you to confirm, and lets you choose whether to apply the change immediately (`switch`) or only on the next reboot (`boot`).
4. Removes the `./result` symlink automatically once the operation finishes, so it does not linger in your working directory.

## Project Structure

```
.
├── flake.nix           # Flake outputs: package, app, and dev shell definitions
├── flake.lock          # Pinned flake inputs
├── main.py             # Entry point, NixOS check, and interactive multi-select menu
├── commands.py         # Command execution, sudo handling, and rebuild/update/gc/search logic
├── system_info.py      # Flake detection and configuration name lookup
├── ui.py               # Minimal custom multi-select widget used by the menu
├── requirements.txt    # Python dependencies
├── LICENSE             # MIT License
└── README.md           # Project documentation
```

## Notes and Caveats

- `Update` on a flake-based system updates all flake inputs at once. If you want more granular control over which inputs get updated, run `nix flake update <input-name>` manually.
- Because NixOS keeps previous generations, a failed or unwanted update can be rolled back from the boot menu, from the `List Generations` menu option, or with `sudo nixos-rebuild switch --rollback`.
- Writing to `/etc/nixos/flake.lock` requires write permission on that file and directory. If the update step fails immediately, check ownership and permissions on `/etc/nixos`.
- If installed with `nix profile add`, remember that it will not auto-update; you must run `nix profile upgrade` with `--refresh` as described above.

## Troubleshooting

- **The tool refuses to start**: Nixctl checks `/etc/os-release` and only runs on NixOS. Confirm you are running it on a NixOS system.
- **Sudo prompt does not appear or hangs**: Ensure your user has sudo privileges configured correctly and that no other process is holding a lock on the Nix store.
- **Update fails immediately on a flake-based system**: Check that you have write permission to `/etc/nixos/flake.lock` and its containing directory.
- **Configuration name not detected**: Verify that `/etc/nixos/flake.nix` defines a valid `nixosConfigurations` output that `nix flake show --json` can read.
- **`nix profile upgrade Nixctl` does nothing**: Make sure you included `--refresh`, and confirm the exact profile entry name and index with `nix profile list` first, since the name is case-sensitive.

## Contributing

Issues and pull requests are welcome. If you are adding a new command, follow the same pattern used by `rebuild()`, `update()`, and `garbage_collect()`:

1. Branch the logic on `uses_flakes()` to determine flake versus legacy behavior.
2. Build the appropriate command list for each case.
3. Pass the resulting command to `run_command()` for execution and progress reporting.
4. If the action changes the running system, build into `./result` and run the diff-before-apply step before switching or booting.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
