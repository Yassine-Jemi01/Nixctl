# Nixctl

Nixctl is a simple interactive CLI tool for **NixOS** maintenance.

It provides a clean terminal interface for common NixOS operations while automatically detecting the system's configuration.

## Version

**0.2.0**

## Features

* **Validate Config** — Check the current NixOS configuration.
* **Rebuild** — Build and apply the current NixOS configuration.
* **Update** — Update Flake inputs and rebuild the system.
* **Garbage Collection** — Remove unused Nix store data.
* **List Generations** — View and delete old NixOS system generations.
* **Search Package** — Search packages available in `nixpkgs`.
* **Flake support** — Automatically detect Flakes and `nixosConfigurations`.
* **Non-Flake support** — Support traditional `/etc/nixos/configuration.nix` systems.
* **Automatic NixOS detection** — Nixctl refuses to run on non-NixOS systems.
* **Clean interface** — Long-running operations display an elapsed-time counter instead of command output.
* **Automatic configuration detection** — No need to manually enter your hostname or Flake configuration name.

## Installation

Install Nixctl directly from GitHub:

```bash
nix profile add github:Yassine-Jemi01/Nixctl
```

Then run:

```bash
nixctl
```

## Updating

Update an installed Nixctl profile with:

```bash
nix profile upgrade Nixctl --refresh
```

## Running from Source

Clone the repository:

```bash
git clone https://github.com/Yassine-Jemi01/Nixctl.git
cd Nixctl
```

Enter the development environment:

```bash
nix develop
```

Then run:

```bash
python main.py
```

## NixOS Support

Nixctl automatically checks whether the current system is NixOS.

For Flake-based systems, it detects the configuration from:

```text
/etc/nixos/flake.nix
```

For example, a configuration such as:

```text
/etc/nixos#yssn
```

can be detected automatically.

For traditional configurations, Nixctl uses:

```text
/etc/nixos/configuration.nix
```

## Generations

Nixctl can display the system's NixOS generations and remove selected old generations.

It uses the NixOS system profile:

```text
/nix/var/nix/profiles/system
```

The current generation is protected from deletion.

After deleting generations, garbage collection can be used to reclaim unused store paths.

## Project Structure

```text
Nixctl/
├── commands.py
├── flake.lock
├── flake.nix
├── LICENSE
├── main.py
├── README.md
├── requirements.txt
├── system_info.py
└── ui.py
```

### `main.py`

Handles application startup, NixOS detection, version information, and the main interface.

### `commands.py`

Contains NixOS operations such as rebuilding, updating, validation, garbage collection, generation management, and package searching.

### `system_info.py`

Handles system detection and information gathering, including Flakes and NixOS generations.

### `ui.py`

Contains the interactive terminal UI components.

## Requirements

Nixctl is designed for NixOS.

When installed through the Flake, Python dependencies are provided automatically.

The project currently uses:

* Python
* Questionary
* Prompt Toolkit
* Nix

## License

Nixctl is licensed under the MIT License.

See [LICENSE](LICENSE) for details.

## Author

**Yassine-Jemi01**

GitHub:
https://github.com/Yassine-Jemi01

Repository:
https://github.com/Yassine-Jemi01/Nixctl
