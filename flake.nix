{
  description = "Nixctl - a simple interactive CLI for NixOS maintenance tasks";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
        };

        pythonEnv = pkgs.python3.withPackages (ps: [
          ps.questionary
          ps.prompt-toolkit
        ]);

        nixctl = pkgs.stdenv.mkDerivation {
          pname = "nixctl";
          version = "0.2.0";

          src = ./.;

          nativeBuildInputs = [
            pkgs.makeWrapper
          ];

          dontBuild = true;

          installPhase = ''
            install -dm755 $out/share/nixctl
            install -dm755 $out/bin

            find src -maxdepth 1 -type f -name '*.py' \
              -exec install -m644 {} $out/share/nixctl/ \;

            makeWrapper ${pythonEnv}/bin/python3 $out/bin/nixctl \
              --add-flags "$out/share/nixctl/main.py" \
              --prefix PATH : ${
                pkgs.lib.makeBinPath [
                  pkgs.nix
                ]
              }
          '';

          meta = with pkgs.lib; {
            description =
              "Interactive CLI for NixOS rebuild, update, and garbage collection";

            homepage =
              "https://github.com/Yassine-Jemi01/Nixctl";

            license = licenses.mit;
            platforms = platforms.linux;
            mainProgram = "nixctl";
          };
        };
      in
      {
        packages.default = nixctl;

        apps.default = {
          type = "app";
          program = "${nixctl}/bin/nixctl";
        };

        devShells.default = pkgs.mkShell {
          packages = [
            pythonEnv
          ];
        };
      });
}