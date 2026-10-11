"""Quick Demo & Scenario Runner for AI Home Renovation Planner.

Allows interactive testing of sample scenarios from the terminal or browser.
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Ensure UTF-8 stdout for Windows terminals
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure .env is loaded
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
SCENARIOS_FILE = BASE_DIR / "sample_inputs" / "sample_scenarios.json"


def show_scenarios():
    if not SCENARIOS_FILE.exists():
        print(f"Scenarios file not found at {SCENARIOS_FILE}")
        return

    with open(SCENARIOS_FILE, "r", encoding="utf-8") as f:
        scenarios = json.load(f)

    print("\n" + "=" * 70)
    print("🏠 AI HOME RENOVATION PLANNER — SAMPLE TEST SCENARIOS")
    print("=" * 70)
    
    for s in scenarios:
        print(f"\n[{s['scenario_id']}] {s['name']}")
        print(f"    Description: {s['description']}")
        if s.get("images"):
            print(f"    Images:      {', '.join(s['images'])}")
        else:
            print("    Images:      None (Text-only)")
        print(f"    Prompt:      \"{s['prompt'][:90]}...\"")
    print("\n" + "=" * 70)


def main():
    show_scenarios()
    print("\n💡 How to use these in the Streamlit App:")
    print("1. Open http://localhost:8501 in your browser.")
    print("2. Click '🍳 Kitchen' or '🛁 Bathroom' in the sidebar, or upload from 'sample_inputs'.")
    print("3. Click '🚀 Run Multi-Agent Renovation Pipeline' to generate your plan.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
