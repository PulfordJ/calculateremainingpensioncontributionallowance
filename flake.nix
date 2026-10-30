{
  description = "Forecast the UK pension annual allowance available in a tax year, with carry forward";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        python3Packages = pkgs.python3Packages;
        # Only files tracked by git are in the flake's source, so a personal
        # contributions.toml (gitignored) never reaches the Nix store.
        pension-allowance = python3Packages.buildPythonApplication {
          pname = "calculateremainingannualpensionallowance";
          version = "2.0";
          pyproject = true;
          src = ./.;
          build-system = [ python3Packages.poetry-core ];
          nativeCheckInputs = [ python3Packages.pytestCheckHook ];
          pythonImportsCheck = [ "calculateremainingannualpensionallowance" ];
          meta.mainProgram = "pension-allowance";
        };
      in
      {
        packages.default = pension-allowance;

        checks.default = pension-allowance;

        devShells.default = pkgs.mkShell {
          packages = [ (pkgs.python3.withPackages (ps: [ ps.pytest ])) ];
        };
      });
}
