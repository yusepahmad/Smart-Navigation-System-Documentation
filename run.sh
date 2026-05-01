#!/usr/bin/env bash
# Smart Navigation System — unified runner
#
# Usage: ./run.sh <command>
#
# Commands:
#   setup       Install / sync dependencies via uv
#   cli         Run Python CLI
#   ui          Run Streamlit UI
#   test        Run test suite
#   c-build     Compile C source with gcc (Linux/Mac)
#   cpp-build   Compile C++ source with g++ (Linux/Mac)
#   c-run       Run compiled C binary
#   help        Show this help message

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
C_DIR="$SCRIPT_DIR/c"

case "${1:-help}" in
  setup)
    echo "→ Installing dependencies with uv..."
    uv sync
    echo "✓ Done. Run ./run.sh cli or ./run.sh ui to start."
    ;;
  cli)
    echo "→ Starting Python CLI..."
    uv run python app/main.py
    ;;
  ui)
    echo "→ Starting Streamlit UI..."
    uv run streamlit run app/streamlit_app.py
    ;;
  test)
    echo "→ Running test suite..."
    uv run python -m unittest discover -s tests -v
    ;;
  c-build)
    echo "→ Compiling cli_app.c with gcc..."
    gcc -O2 -o "$C_DIR/cli_app" "$C_DIR/cli_app.c" -lm
    echo "✓ Binary created: c/cli_app"
    echo "  Run with: ./run.sh c-run"
    ;;
  cpp-build)
    echo "→ Compiling cli_app.cpp with g++..."
    g++ -std=c++17 -O2 -o "$C_DIR/cli_app_cpp" "$C_DIR/cli_app.cpp"
    echo "✓ Binary created: c/cli_app_cpp"
    ;;
  c-run)
    if [ ! -f "$C_DIR/cli_app" ]; then
      echo "✗ Binary not found. Run './run.sh c-build' first."
      exit 1
    fi
    echo "→ Running C binary..."
    "$C_DIR/cli_app"
    ;;
  help|*)
    echo ""
    echo "Smart Navigation System — runner"
    echo ""
    echo "Usage: ./run.sh <command>"
    echo ""
    echo "  setup      Install / sync dependencies via uv"
    echo "  cli        Run Python CLI"
    echo "  ui         Run Streamlit UI"
    echo "  test       Run test suite"
    echo "  c-build    Compile C source with gcc (Linux/Mac)"
    echo "  cpp-build  Compile C++ source with g++ (Linux/Mac)"
    echo "  c-run      Run compiled C binary"
    echo "  help       Show this message"
    echo ""
    echo "Windows users: see docs/GUIDE.md section 4.B for MSVC setup."
    echo ""
    ;;
esac
