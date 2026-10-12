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


def show_langgraph_info():
    from renovation_engine import get_graph_mermaid_diagram, renovation_graph
    print("\n" + "=" * 70)
    print("🕸️ LANGGRAPH MULTI-AGENT ARCHITECTURE")
    print("=" * 70)
    print(f"Nodes in StateGraph ({len(renovation_graph.nodes)}):")
    for node in renovation_graph.nodes:
        print(f"  • {node}")
    print("\nMermaid Flowchart:")
    print(get_graph_mermaid_diagram())
    print("=" * 70)


def run_scenario_cli(scenario_id: str):
    from renovation_engine import stream_renovation_graph, RenovationState
    from PIL import Image

    if not SCENARIOS_FILE.exists():
        print(f"Scenarios file not found at {SCENARIOS_FILE}")
        return

    with open(SCENARIOS_FILE, "r", encoding="utf-8") as f:
        scenarios = json.load(f)

    target = next((s for s in scenarios if s.get("scenario_id") == scenario_id), None)
    if not target:
        print(f"❌ Scenario '{scenario_id}' not found.")
        return

    print(f"\n🚀 Running Scenario '{scenario_id}': {target['name']} via LangGraph...")
    
    current_image = None
    inspiration_image = None
    img_list = target.get("images", [])
    if len(img_list) > 0 and (BASE_DIR / "sample_inputs" / img_list[0]).exists():
        current_image = Image.open(BASE_DIR / "sample_inputs" / img_list[0])
    if len(img_list) > 1 and (BASE_DIR / "sample_inputs" / img_list[1]).exists():
        inspiration_image = Image.open(BASE_DIR / "sample_inputs" / img_list[1])

    state: RenovationState = {
        "mode": "full",
        "user_prompt": target["prompt"],
        "room_type": "Kitchen" if "kitchen" in target["name"].lower() else "Bathroom",
        "target_style": "Modern Farmhouse",
        "budget_raw": "$15,000",
        "current_image": current_image,
        "inspiration_image": inspiration_image,
        "skip_rendering": True,
        "execution_history": [],
    }

    try:
        for node_name, update in stream_renovation_graph(state):
            print(f"  ✅ Completed LangGraph Node: [{node_name}]")
        print("\n🎉 LangGraph pipeline execution complete!")
    except Exception as e:
        print(f"\n⚠️ Pipeline run halted: {e}")


def main():
    show_scenarios()
    show_langgraph_info()
    if len(sys.argv) > 1 and sys.argv[1] == "--run":
        sc_id = sys.argv[2] if len(sys.argv) > 2 else "scenario_1"
        run_scenario_cli(sc_id)
    else:
        print("\n💡 How to use:")
        print("1. Streamlit App: Run `streamlit run app.py`")
        print("2. Test LangGraph CLI: Run `python run_demo.py --run scenario_1`")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
