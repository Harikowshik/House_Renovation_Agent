# 🏚️ 🍌 AI Home Renovation Planner (Streamlit App)

An end-to-end multi-agent renovation planning and visual intelligence suite powered directly by the **Google GenAI** (`gemini-3-flash-preview`) and **Streamlit**. Upload real room photos and inspiration styles, preserve your physical layout, calculate itemized budgets and ROI, analyze DIY savings, and export print-ready PDF and Markdown dossiers.

---

## 🧠 System Architecture Overview

The system orchestrates specialized agent personas sequentially to turn amateur room photos into professional contractor briefs:

```
                            ┌───────────────────────────────────────────────┐
                            │            USER INPUT & MULTIMODAL            │
                            │  Room Photo(s) + Inspiration Photo + Prompt   │
                            └───────────────────────┬───────────────────────┘
                                                    │
                                                    ▼
                            ┌───────────────────────────────────────────────┐
                            │        DYNAMIC INTENT & BUDGET PARSER         │
                            │  - Regex Prompt Budget Extraction ($Xk)       │
                            │  - Min-Money / Zero-Paint / Staging Detection │
                            │  - Duplicate Image Hash Matching              │
                            └───────────────────────┬───────────────────────┘
                                                    │
                 ┌──────────────────────────────────┼──────────────────────────────────┐
                 ▼                                  ▼                                  ▼
      ┌─────────────────────┐            ┌────────────────────┐            ┌──────────────────────┐
      │  1. VisualAssessor  │            │  2. DesignPlanner  │            │3. ProjectCoordinator │
      │ - 360° Layout Lock  │ ─────────▶ │ - Specific Finishes│ ─────────▶ │ - Itemized Roadmap   │
      │ - Window/Door Spans │            │ - Benjamin Moore   │            │ - Stretch Tier (+$X) │
      │ - Style Extraction  │            │ - Staging Guidance │            │ - SLC 8K Render Brief│
      └─────────────────────┘            └────────────────────┘            └──────────┬───────────┘
                                                                                      │
                 ┌──────────────────────────────────┬─────────────────────────────────┘
                 ▼                                  ▼
      ┌─────────────────────┐            ┌────────────────────┐
      │ 4. Analytics Suite  │            │ 5. Dual Exporter   │
      │ - Palette & HEX     │            │ - Print PDF (fpdf2)│
      │ - Resale ROI & Equity│           │ - Full Markdown    │
      │ - Material Quantities│           │ - Contractor RFQ   │
      │ - DIY vs Pro Labor  │            │                    │
      └─────────────────────┘            └────────────────────┘
```

---

## 📖 Complete Workflows Guide (Topic-by-Topic)

### Workflow 1: Dynamic Prompt Budget Extraction & Prioritization
* **The Challenge**: Users frequently type their budget directly in natural language (e.g. *"I only have $8k"*, *"under 12,000 dollars"*, or *"budget: $3,500"*), which should not be ignored in favor of a sidebar default.
* **How It Works**:
  1. The regex parser detects amounts in various formats (`$Xk`, `Xk`, `$X,XXX`, `XXXX dollars`).
  2. If found, the extracted amount **automatically overrides** the sidebar slider and becomes the primary financial constraint.
  3. The UI immediately displays a confirmation badge: `🎯 Budget Detected in Prompt: $8,000 (Overriding sidebar default)`.
  4. All downstream agent specifications (materials, labor, contingency) are strictly scaled to fit this exact number.

---

### Workflow 2: The "Stretch Budget" Upgrade Tier (+20% Investment)
* **The Concept**: Homeowners often don't know where a tiny incremental budget boost provides the biggest bang for the buck.
* **How It Works**:
  1. The `DesignPlanner` and `ProjectCoordinator` build the baseline plan to fit 100% within the user's primary budget.
  2. The agents append a dedicated **`🚀 STRETCH BUDGET UPGRADES`** section.
  3. Identifies the 2–3 highest-leverage add-ons if the user can stretch by $1,000 – $3,000 (e.g., solid slab quartz vs. laminate, hardwired under-cabinet LED channels, or professional cabinet lacquer spraying).
  4. Explains why this small stretch yields disproportionately high visual and durability returns.

---

### Workflow 3: Minimum Money / Shoestring Budget Mode ("Min-Cost" Priority)
* **Trigger Phrases**: *"cheapest possible"*, *"min money"*, *"lowest cost"*, *"bare minimum budget"*, *"shoestring"*.
* **How It Works**:
  1. The engine detects the minimum-cost intent and shifts prioritization.
  2. **Tier 1 (Bare Minimum / Sweat Equity)**: Prioritizes zero-to-low-cost interventions: deep cabinet degreasing, DIY spray-painting existing hardware, regrouting tile, and decluttering.
  3. **Tier 2 (Micro Step-Up)**: Suggests targeted investments of $150 – $400 for high-impact visual improvements (e.g., peel-and-stick backsplash tile, new faucet, modern light fixture).

---

### Workflow 4: Zero-Paint & Zero-Ceiling Staging Mode
* **Trigger Phrases**: *"don't paint"*, *"not to modify the painting"*, *"leave ceiling"*, *"just move existing things"*, *"rearrange only"*.
* **How It Works**:
  1. The engine locks existing wall paint, cabinet finishes, and ceilings into **Protected Status**.
  2. The `DesignPlanner` strictly prohibits wall or cabinet paint recommendations.
  3. **Spatial Realignment**: Focuses on repositioning existing movable furniture, kitchen carts, island stools, and open shelving items to match the inspiration photo composition.
  4. **Surface Styling & Staging**: Specifies countertop accessory arrangements (cutting boards, canisters, runner rugs, indoor plants) to mirror the inspiration aesthetic without altering surfaces.

---

### Workflow 5: Single Photo vs. Dual Photo Renovation Modes
* **Single Room Photo Uploaded**:
  - `VisualAssessor` inspects wear-and-tear, layout bottlenecks, and outdated elements.
  - Proposes 2–3 cohesive design directions (e.g., Modern Farmhouse, Japandi, Warm Minimalist) suited to the room's lighting and footprint.
* **Dual Photos (Current Room + Inspiration Photo)**:
  - `VisualAssessor` cross-compares both photos.
  - Extracts the exact color palette, stone veining, wood tones, and hardware styles from the inspiration image and maps them onto the current room's layout.

---

### Workflow 6: Identical Image Handling (Style-Preserving Refresh)
* **What Happens**: If the user uploads the exact same image for both Current Space and Inspiration.
* **How It Works**:
  1. The engine computes byte hashes of both images. If they match, it activates **Style-Preserving Refresh Mode**.
  2. Avoids forcing unnatural style overhauls onto a room the user clearly likes.
  3. Focuses on cosmetic restoration: refreshing sealants, repairing chipping, upgrading to durable quartz in the same undertone, and installing energy-efficient warm LED fixtures.

---

### Workflow 7: Whole-Home Adjoining Room Cohesion
* **The Scenario**: User uploads an already-renovated dining room or living room in their home as the inspiration for an outdated kitchen.
* **How It Works**:
  1. The agent identifies the house's architectural DNA.
  2. **Flooring Transitions**: Matches plank width, wood species, and stain to ensure seamless threshold transitions.
  3. **Millwork Alignment**: Coordinates baseboard height, door casings, and trim styles.
  4. **Hardware Language**: Keeps metal finishes (e.g., matte black or warm brass) consistent across both spaces.

---

### Workflow 8: Multi-Angle Spatial Fusion
* **The Scenario**: User uploads two different camera angles of the same unfinished space.
* **How It Works**:
  1. `VisualAssessor` cross-references both viewpoints (e.g., sink wall + stove/refrigerator wall).
  2. Synthesizes a **360° layout map**, capturing cabinet runs, appliance locations, and doorways that would otherwise be hidden behind a single camera lens.
  3. Ensures higher accuracy in rendering prompts and material quantity estimates.

---

### Workflow 9: Resale Value & Home ROI Estimator
* **How It Works**:
  1. Applies real estate industry cost-vs-value ratios based on room type:
     - Minor/Moderate Kitchen Refresh: ~78% recovery rate
     - Master Bathroom Remodel: ~68% recovery rate
     - Guest Bathroom: ~71% recovery rate
     - Living Room / Bedroom Refresh: ~60%–62% recovery rate
  2. Calculates:
     - **Estimated Home Equity Value Added ($)**
     - **Expected Resale ROI (%)**
     - **Net Effective Renovation Cost** ($\text{Budget} - \text{Equity Gain}$)

---

### Workflow 10: Room Dimensions & Material Quantity Estimator
* **Input**: Room Length ($ft$), Width ($ft$), and Ceiling Height ($ft$).
* **How It Works**:
  1. $\text{Floor Area} = \text{Length} \times \text{Width}$
  2. $\text{Wall Area} = 2 \times (\text{Length} + \text{Width}) \times \text{Height} \times 0.85$ (net of openings)
  3. **Paint**: $\text{Gallons} = (\text{Wall Area} \times 2) / 375$ (two full coats)
  4. **Flooring**: $\text{Sq Ft} \times 1.10$ (+10% cutting waste factor) $\rightarrow$ calculates boxes needed (22 sq ft/box)
  5. **Tile/Backsplash**: Calculated with +15% waste factor for complex patterns (herringbone, subway).

---

### Workflow 11: DIY vs. Licensed Pro Feasibility Breakdown
* **How It Works**:
  1. Analyzes each trade task in the design plan.
  2. **🟢 DIY-Friendly Tasks**: Low risk, high sweat equity (cabinet painting, hardware swaps, peel-and-stick backsplash, caulking).
  3. **🔴 Licensed Pro Tasks**: Code compliance and structural safety (electrical rough-ins, plumbing relocation, slab countertop templating & fabrication).
  4. **Labor Savings Metric**: Calculates estimated cash savings ($1,200 – $3,500+) if you do the cosmetic labor yourself.

---

### Workflow 12: 1-Click Contractor RFQ Email Generator
* **How It Works**:
  1. Generates a formal Request for Quotation (RFQ) formatted for contractor bids.
  2. Features:
     - Scope of work breakdown
     - Strict layout preservation clause (preventing unneeded demolition quotes)
     - Credential checklist (license, liability insurance, workman's comp)
     - Milestone-based payment schedule request (Deposit, Rough-in, Substantial Completion, Final Punch List)

---

### Workflow 13: 24/7 AI Renovation Consultant & Live Refinement
* **How It Works**:
  - **Builder Q&A**: Ask any technical question (*"Can I paint over oak cabinets without stripping to bare wood?"*, *"What underlayment is needed for vinyl plank?"*, or *"Do I need a building permit?"*).
  - **Conversational Refinement**: Type design tweaks (*"Make the cabinets dark green"*, *"Switch hardware to matte black"*) and the agent immediately re-specifies materials and regenerates color swatches.

---

### Workflow 14: Dual Dossier Export (Print-Ready PDF + Markdown)
* **Print-Ready PDF (`.pdf`)**:
  - Executive header banner and metadata summary card.
  - Material quantity table.
  - Section headers with styling and paragraphs.
  - Built with `fpdf2`.
* **Complete Markdown (`.md`)**:
  - Full-text Markdown dossier ready for Notion, GitHub, or digital note-taking.

---

## 🚀 Quick Start

### 1. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 2. Set Up Your API Key
In [.env](file:///c:/Users/harik/OneDrive/Desktop/Home%20Renovation%20Agent/.env):
```env
GOOGLE_API_KEY="your_gemini_api_key"
```

### 3. Launch Streamlit
```powershell
streamlit run app.py
```
Open **[http://localhost:8501](http://localhost:8501)** in your web browser.

---

## 📁 Project Structure

```
Home Renovation Agent/
├── app.py                  # Streamlit application UI, badges, and dashboard
├── renovation_engine.py    # Direct multi-agent orchestration engine (Google GenAI)
├── pdf_generator.py        # Print-ready PDF report generator (fpdf2)
├── run_demo.py             # CLI scenario runner
├── requirements.txt        # Clean dependencies (google-genai, streamlit, pillow, fpdf2)
├── .env                    # API key configuration
├── .gitignore              # Git ignore rules
├── README.md               # Complete workflows and documentation
└── sample_inputs/          # High-resolution sample images and prompts
    ├── outdated_kitchen.jpg
    ├── kitchen_inspiration.jpg
    ├── outdated_bathroom.jpg
    ├── bathroom_inspiration.jpg
    └── sample_scenarios.json
```
