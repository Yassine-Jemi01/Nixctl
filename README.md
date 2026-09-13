# Nixctl

An interactive command-line tool for day-to-day NixOS maintenance: rebuilding, updating, cleaning up the store, managing generations, searching packages, and validating your configuration. Built as a menu-driven wrapper around `nixos-rebuild` and `nix`, so you don't have to remember the exact flags for your setup.

## Features

- **Rebuild** — Builds your current configuration, shows a diff of what would change, then lets you apply it (switch now or on next boot).
- **Update** — On flake-based systems, refreshes `flake.lock` before building. On legacy systems, runs a build with `--upgrade`. Then follows the same build → diff → confirm → apply flow as Rebuild.
- **Garbage Collection** — Frees up disk space with `nix-collect-garbage --delete-old` (flakes) or `nix-store --gc` (legacy).
- **List Generations** — Lists system generations and lets you select one or more to delete (the current generation is protected and cannot be selected).
- **Search Package** — Searches nixpkgs by name and prints matching packages with their version and description.
- **Validate Config** — Checks your configuration for errors (`nix flake check` or `nixos-rebuild dry-build`) before you commit to a full rebuild.
- **Diff before applying** — Every rebuild or update builds the new system first, then shows a `nix store diff-closures` comparison against the currently running system before anything is activated.
- **Switch or boot** — Choose whether a change takes effect immediately or on the next reboot.
- **Multi-select menu** — Select multiple actions at once with the spacebar (for example, validate, then update, then collect garbage, in one pass) and confirm with Enter. It's a minimal custom widget with no "select all" or "invert" shortcuts — Space is the only way to change a selection.
- **Automatic flake detection** — Detects `/etc/nixos/flake.nix` and reads `nixosConfigurations` to determine the configuration name automatically, with no hardcoding required.
- **Sudo requested up front** — Authentication happens before any command runs, including flake updates, so you're never interrupted mid-operation.
- **Live progress feedback** — Shows an elapsed-time counter while a command runs and reports success or failure when it finishes.
- **NixOS-only safeguard** — Checks `/etc/os-release` on startup and refuses to run on non-NixOS systems.

## Requirements

- NixOS
- Python 3.8+
- [questionary](https://pypi.org/project/questionary/)
- [prompt_toolkit](https://pypi.org/project/prompt-toolkit/) (used directly for the custom multi-select menu)
- The `nix-command` experimental feature enabled, for diffing, searching, and flake checks:

  ```nix
  nix.settings.experimental-features = [ "nix-command" "flakes" ];
  ```

## Installation

### With Nix (recommended)

Run it directly without installing anything:

```bash
nix run github:Yassine-Jemi01/Nixctl
```

Install it into your profile:

```bash
nix profile add github:Yassine-Jemi01/Nixctl
```

Don't pin the install to a specific commit (e.g. `.../Nixctl/<commit-hash>`) — that locks you to that exact commit forever and `upgrade` won't move past it. Using the plain URL above always resolves to the latest `main` at install time, and lets `nix profile upgrade` pull newer commits later.

You can also add it as an input to your own system flake and include the package in `environment.systemPackages`.

### Manual install

```bash
git clone https://github.com/Yassine-Jemi01/Nixctl.git
cd Nixctl
pip install -r requirements.txt
```

## Usage

If installed via Nix:

```bash
nixctl
```

Otherwise, run it directly with Python:

```bash
python main.py
```

You'll see a menu like this:

```
? What do you want to do?
  > [ ] Validate Config
    [ ] Rebuild
    [ ] Update
    [ ] Garbage Collection
    [ ] List Generations
    [ ] Search Package

  >  current row    [x] selected    [ ] not selected    space: toggle    enter: confirm
```

Use the arrow keys to move, **Space** to select one or more actions, and **Enter** to run them. This is a minimal custom selector (see `ui.py`) — only Space toggles a selection; there's no "select all" or "invert selection" shortcut, so nothing gets picked by accident. Leaving nothing selected and pressing Enter, or pressing Esc/Ctrl+C, exits the tool.

Selected actions always run in a fixed order — Validate Config first, then Rebuild, Update, Garbage Collection, List Generations, Search Package — regardless of the order you picked them in.

For Rebuild and Update, once the build finishes you'll see a diff of what's about to change, then be asked to confirm and choose between applying it immediately (switch) or on next boot.

## Updating Nixctl itself

If you installed it with `nix profile add`, it won't pick up new versions on its own — you need to refresh it explicitly once new commits are pushed to `main`:

```bash
nix profile list
nix profile upgrade Nixctl --refresh
```

Nix names the profile entry after the flake's repository, so the name is case-sensitive — check the exact name (and index) with `nix profile list` first. If `upgrade Nixctl` doesn't match, use the index shown instead:

```bash
nix profile upgrade <index> --refresh
```

`--refresh` is required — without it, Nix reuses its local evaluation cache instead of checking GitHub for new commits, and the upgrade silently does nothing.

## Removing Nixctl

```bash
nix profile remove Nixctl
```

Or by index, if `remove` doesn't accept the name directly:

```bash
nix profile list
nix profile remove <index>
```

## How it works

The tool checks for `/etc/nixos/flake.nix` to decide which code path to use:

| Task | Flake-based system | Legacy system |
|---|---|---|
| Build | `sudo nixos-rebuild build --flake /etc/nixos#<name>` | `sudo nixos-rebuild build -I nixos-config=/etc/nixos/configuration.nix` |
| Update (before build) | `nix flake update --flake /etc/nixos` | build runs with `--upgrade` |
| Diff | `nix store diff-closures /run/current-system ./result` | same |
| Apply | `sudo nixos-rebuild switch\|boot --flake /etc/nixos#<name>` | `sudo nixos-rebuild switch\|boot -I nixos-config=...` |
| Garbage Collection | `nix-collect-garbage --delete-old` | `nix-store --gc` |
| List Generations | `nix-env --list-generations -p /nix/var/nix/profiles/system` | same |
| Delete Generations | `sudo nix-env --delete-generations <ids> -p /nix/var/nix/profiles/system` | same |
| Search | `nix search nixpkgs <query> --json` | same |
| Validate | `nix flake check /etc/nixos` | `nixos-rebuild dry-build -I nixos-config=...` |

When using flakes, the configuration name is read directly from the output of `nix flake show --json /etc/nixos`, so it never needs to be hardcoded.

Rebuild and Update never activate a new system blindly: they build it into `./result` first, diff it against `/run/current-system`, and only apply it after you confirm. The `./result` symlink is cleaned up automatically once the operation finishes.

## Project structure

```
.
├── main.py           # Entry point, NixOS check, and the multi-select menu
├── commands.py       # Command execution, sudo handling, build/diff/apply flow, generations, search, validation
├── system_info.py    # Flake detection, configuration name lookup, generations, package search
├── ui.py             # Minimal custom multi-select prompt (arrows, space, enter — no other shortcuts)
├── flake.nix          # Nix package/app definition for `nix run` / `nix profile add`
├── flake.lock         # Pinned versions of flake inputs (nixpkgs, flake-utils)
└── requirements.txt
```

## Notes and caveats

- `Update` on a flake-based system updates **all** flake inputs at once. For finer control, run `nix flake update <input-name>` manually instead.
- Diffing, searching, and config validation require the `nix-command` experimental feature. If it isn't enabled, those steps report an error instead of crashing.
- Because NixOS keeps previous generations, a failed or unwanted update can still be rolled back from the boot menu or with `sudo nixos-rebuild switch --rollback`, independently of anything this tool does.
- Writing to `/etc/nixos/flake.lock` requires write permission on that file or directory. If the update step fails immediately, check ownership and permissions on `/etc/nixos`.
- The current generation is protected in the generations list and cannot be selected for deletion.
- For maintainers: always commit and push `flake.lock` alongside `flake.nix`. Without it committed to `main`, `nix profile add`/`upgrade` has no lock file to resolve against and users can hit lock-file errors.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Issues and pull requests are welcome. If you're adding a new command, follow the existing pattern: branch on `uses_flakes()` where relevant, use `run_command()` for anything long-running with live feedback, and `run_and_capture()` for quick informational commands whose output needs to be read (diffing, searching, validating).
