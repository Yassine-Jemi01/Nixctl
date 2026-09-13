{
  description = "Nixctl - a simple interactive CLI for NixOS maintenance tasks";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };

        pythonEnv = pkgs.python3.withPackages (ps: [ ps.questionary ]);

        nixctl = pkgs.stdenv.mkDerivation {
          pname = "nixctl";
          version = "0.1.0";

          src = ./.;

          nativeBuildInputs = [ pkgs.makeWrapper ];

          dontBuild = true;

          installPhase = ''
            mkdir -p $out/share/nixctl $out/bin
            cp main.py commands.py system_info.py $out/share/nixctl/

            makeWrapper ${pythonEnv}/bin/python3 $out/bin/nixctl \
              --add-flags "$out/share/nixctl/main.py"
          '';

          meta = with pkgs.lib; {
            description = "Interactive CLI for NixOS rebuild, update, and garbage collection";
            homepage = "https://github.com/Yassine-Jemi01/Nixctl";
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
          packages = [ pythonEnv ];
        };
      });
}
