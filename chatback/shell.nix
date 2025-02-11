{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    stdenv.cc.cc.lib  # Provides libstdc++
    stdenv.cc.cc      # GCC with libstdc++
    gcc
    python312
    postgresql
    openssl
    zlib
    grpc
  ];

  shellHook = ''
    export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
    export PYTHONPATH=$PWD:$PYTHONPATH
  '';
}
