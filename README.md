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
python src/main.py
```

## Project Structure

```text
Nixctl/
├── src/
│   ├── commands.py
│   ├── main.py
│   ├── system_info.py
│   └── ui.py
├── flake.lock
├── flake.nix
├── LICENSE
├── README.md
└── requirements.txt
```

### `src/main.py`

Handles application startup, NixOS detection, version information, and the main interface.

### `src/commands.py`

Contains NixOS operations such as rebuilding, updating, validation, garbage collection, generation management, and package searching.

### `src/system_info.py`

Handles system detection and information gathering, including Flakes and NixOS generations.

### `src/ui.py`

Contains the interactive terminal UI components.
