# NixOS CLI

A simple interactive command-line tool for common NixOS system maintenance tasks: rebuilding your configuration, updating it, and cleaning up the Nix store. Built with a menu-driven interface so you don't have to remember the exact `nixos-rebuild` and `nix` invocations for your setup.

## Features

- **Rebuild** — Applies your current NixOS configuration with `nixos-rebuild switch`, automatically detecting whether you use a flake-based setup or the legacy `configuration.nix` setup.
- **Update** — Pulls in new package versions. On flake-based systems this runs `nix flake update` to refresh `flake.lock` before rebuilding; on legacy systems it runs `nixos-rebuild switch --upgrade`.
- **Garbage Collection** — Frees up disk space by removing old generations and unused store paths, using `nix-collect-garbage --delete-old` (flakes) or `nix-store --gc` (legacy).
- **Automatic flake detection** — Detects whether `/etc/nixos/flake.nix` exists and reads the flake's `nixosConfigurations` to determine the correct configuration name automatically.
- **Live progress feedback** — Shows an elapsed-time counter while a command runs, and reports success or failure when it finishes.
- **Safe sudo handling** — Prompts for your sudo password up front, before starting any timed operation, so authentication delays don't get counted as part of the command's runtime.
- **NixOS-only safeguard** — Checks `/etc/os-release` on startup and refuses to run on non-NixOS systems.

## Requirements

- NixOS
- Python 3.8+
- [questionary](https://pypi.org/project/questionary/)

## Installation

Clone the repository and install the Python dependency:

```bash
git clone https://github.com/<your-username>/nixos-cli.git
cd nixos-cli
pip install -r requirements.txt
```

## Usage

Run the tool with:

```bash
python main.py
```

You'll be shown a menu with the following options:

```
What do you want to do?
  Rebuild
  Update
  Garbage Collection
  Exit
```

Use the arrow keys to select an option and press Enter. Operations that require elevated privileges will prompt for your sudo password before starting.

## How it works

The tool checks for the presence of `/etc/nixos/flake.nix` to decide which code path to take:

| Task | Flake-based system | Legacy system |
|---|---|---|
| Rebuild | `sudo nixos-rebuild switch --flake /etc/nixos#<name>` | `sudo nixos-rebuild switch -I nixos-config=/etc/nixos/configuration.nix` |
| Update | `nix flake update` then rebuild with the flake | `sudo nixos-rebuild switch --upgrade` |
| Garbage Collection | `nix-collect-garbage --delete-old` | `nix-store --gc` |

When using flakes, the configuration name is read directly from the output of `nix flake show --json /etc/nixos`, so you don't need to hardcode it anywhere.

## Project structure

```
.
├── main.py           # Entry point, NixOS check, and interactive menu
├── commands.py       # Command execution, sudo handling, and rebuild/update/gc logic
├── system_info.py    # Flake detection and configuration name lookup
└── requirements.txt
```

## Notes and caveats

- `Update` on a flake-based system updates **all** flake inputs at once. If you want more granular control over which inputs get updated, you'll need to run `nix flake update <input-name>` manually.
- Because NixOS keeps previous generations, a failed or unwanted update can be rolled back from the boot menu or with `sudo nixos-rebuild switch --rollback`.
- Writing to `/etc/nixos/flake.lock` requires write permission on that file/directory. If the update step fails immediately, check ownership and permissions on `/etc/nixos`.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Issues and pull requests are welcome. If you're adding a new command, keep the same pattern used by `rebuild()`, `update()`, and `garbage_collect()`: branch on `uses_flakes()`, build the appropriate command list, and pass it to `run_command()`.
