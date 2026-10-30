{
  description = "Forecast the UK pension annual allowance available in a tax year, with carry forward";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.uv2nix.follows = "uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, flake-utils, pyproject-nix, uv2nix, pyproject-build-systems }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
        };

        # Load the workspace from uv.lock. Only files tracked by git are in the
        # flake's source, so a personal contributions.toml (gitignored) never
        # reaches the Nix store.
        workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };

        # Create overlay with build systems
        overlay = workspace.mkPyprojectOverlay {
          sourcePreference = "wheel";
        };

        # Create the Python package set
        python = pkgs.python311;
        pythonSet = (pkgs.callPackage pyproject-nix.build.packages {
          inherit python;
        }).overrideScope(
          pkgs.lib.composeManyExtensions [
            pyproject-build-systems.overlays.default
            overlay
          ]
        );

        # Build the virtual environment
        venv = pythonSet.mkVirtualEnv "pension-allowance-env" workspace.deps.all;

        # Bootstrap shell (for generating uv.lock before venv exists)
        bootstrapShell = pkgs.mkShell {
          packages = [
            pkgs.uv
            python
          ];
        };

      in
      {
        # App for running the calculator
        apps.default = {
          type = "app";
          program = "${venv}/bin/pension-allowance";
        };

        # Development shell with full environment
        devShells.default = pkgs.mkShell {
          packages = [
            venv
            pkgs.uv
          ];

          shellHook = ''
            # Ensure we use the virtual environment's Python
            export VIRTUAL_ENV="${venv}"
            export PATH="${venv}/bin:$PATH"

            echo "💷 Pension annual allowance environment loaded"
            echo "   Python: $(python --version)"
            echo ""
            echo "Quick start:"
            echo "   pytest              - run the test suite"
            echo "   nix run             - forecast from contributions.toml"
            echo "   nix run -- --help   - options"
          '';
        };

        # Bootstrap shell (for initial setup without uv.lock)
        devShells.bootstrap = bootstrapShell;

        # Package the environment
        packages.default = venv;

        # Run the tests against the source tree in the sandbox
        checks.default = pkgs.runCommand "pension-allowance-tests" { } ''
          cp -r ${./.} src
          chmod -R u+w src
          cd src
          ${venv}/bin/pytest -q -p no:cacheprovider
          touch $out
        '';
      }
    );
}
