"""AI Home Renovation Planner - Multi-Agent Engine (Direct Google GenAI SDK)

Implements the multi-agent renovation planning workflow:
1. VisualAssessor: Vision AI analyzing room photos, locking physical layout, extracting styles.
2. DesignPlanner: Surface finish specialist specifying materials, colors, and hardware.
3. ProjectCoordinator: Budget breakdown, timeline, contractor checklist, and SLC rendering prompt.
4. RenderingRefiner: Handles iterative delta modifications.
5. ColorPaletteExtractor: Extracts structured HEX color swatches and materials.
6. DIYvsProAnalyzer: Categorizes tasks into DIY savings vs licensed pro trades.
7. ContractorRFQGenerator: Creates professional Request for Quotation emails/briefs.
8. RenovationConsultant: 24/7 expert builder Q&A for permits, materials, and prep.
"""

import os
import json
import re
import logging
from typing import Optional, Dict, Any, Tuple, List
from PIL import Image
import io

from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

DEFAULT_VISION_MODEL = "gemini-3-flash-preview"
FALLBACK_VISION_MODEL = "gemini-2.5-flash"


def get_genai_client(api_key: Optional[str] = None) -> genai.Client:
    """Create a Google GenAI client using provided or environment API key."""
    key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError("Google Gemini API key not found. Please provide an API key.")
    return genai.Client(api_key=key)


def image_to_part(image_input) -> types.Part:
    """Convert a PIL Image, bytes, or file path to a types.Part for Google GenAI."""
    if isinstance(image_input, types.Part):
        return image_input
        
    if isinstance(image_input, str):
        with open(image_input, "rb") as f:
            data = f.read()
        mime = "image/jpeg" if image_input.lower().endswith((".jpg", ".jpeg")) else "image/png"
        return types.Part.from_bytes(data=data, mime_type=mime)
        
    if isinstance(image_input, bytes):
        return types.Part.from_bytes(data=image_input, mime_type="image/jpeg")
        
    if isinstance(image_input, Image.Image):
        buf = io.BytesIO()
        image_input.save(buf, format="JPEG", quality=90)
        return types.Part.from_bytes(data=buf.getvalue(), mime_type="image/jpeg")
        
    raise ValueError(f"Unsupported image input type: {type(image_input)}")


def extract_budget_from_prompt(prompt: str, fallback_budget: str = "$15,000") -> Tuple[str, float, bool]:
    """
    Extracts explicit budget mentioned in the user's prompt text.
    Returns (formatted_budget_str, budget_float, was_found_in_prompt).
    Handles:
    - $5000, $5,000, $5k, $5.5k
    - 5k, 12 thousand, 7000 dollars/bucks
    """
    if not prompt:
        num = float(re.sub(r"[^\d.]", "", fallback_budget) or 15000)
        return fallback_budget, num, False

    p = prompt.lower()
    
    # 1. $Xk or $X.Xk
    m = re.search(r"\$\s*(\d+(?:\.\d+)?)\s*k\b", p)
    if m:
        val = float(m.group(1)) * 1000
        return f"${val:,.0f}", val, True

    # 2. Xk or X.Xk budget / dollars
    m = re.search(r"\b(\d+(?:\.\d+)?)\s*k\s*(?:budget|dollars|bucks)?\b", p)
    if m:
        val = float(m.group(1)) * 1000
        return f"${val:,.0f}", val, True

    # 3. $X,XXX or $XXXX
    m = re.search(r"\$\s*(\d{1,3}(?:,\d{3})+|\d+)", p)
    if m:
        val = float(m.group(1).replace(",", ""))
        return f"${val:,.0f}", val, True

    # 4. XXXX dollars / budget
    m = re.search(r"\b(\d{3,7})\s*(?:dollars|bucks|budget)\b", p)
    if m:
        val = float(m.group(1))
        return f"${val:,.0f}", val, True

    # Fallback
    num = float(re.sub(r"[^\d.]", "", fallback_budget) or 15000)
    return fallback_budget, num, False


def detect_renovation_intents(user_prompt: str) -> Dict[str, bool]:
    """Detects specific user constraints like minimal cost priority or no-paint/rearrange-only."""
    p = (user_prompt or "").lower()
    
    is_min_money_mode = any(k in p for k in [
        "min money", "minimum", "minimal", "lowest cost", "cheapest", 
        "as cheap as possible", "bare minimum", "shoestring", "least amount", "least cost"
    ])
    
    is_no_paint_mode = any(k in p for k in [
        "no paint", "don't paint", "dont paint", "not to modify the paint",
        "not to modify the painting", "keep painting", "keep current paint", "leave paint", "not paint"
    ])
    
    is_no_ceiling_mode = any(k in p for k in [
        "no ceiling", "don't touch ceiling", "dont touch ceiling", "leave ceiling", "keep ceiling", "not modify ceiling"
    ])
    
    is_rearrange_only_mode = any(k in p for k in [
        "just move", "move the things", "rearrange", "staging only", "just rearrange", "move things that already exist"
    ])
    
    return {
        "min_money_mode": is_min_money_mode,
        "no_paint_mode": is_no_paint_mode,
        "no_ceiling_mode": is_no_ceiling_mode,
        "rearrange_only_mode": is_rearrange_only_mode or (is_no_paint_mode and is_no_ceiling_mode),
    }


# ============================================================================
# Specialist 1: Visual Assessor Agent
# ============================================================================

def assess_room_and_inspiration(
    client: genai.Client,
    current_image: Optional[Any],
    inspiration_image: Optional[Any],
    user_prompt: str,
    room_type: str = "Kitchen",
    budget: str = "$15,000",
    model: str = DEFAULT_VISION_MODEL,
) -> str:
    """Analyzes room photos and inspiration images using Gemini Multimodal Vision."""
    # Check if images are identical
    is_same_image = False
    if current_image is not None and inspiration_image is not None:
        try:
            if hasattr(current_image, "tobytes") and hasattr(inspiration_image, "tobytes"):
                is_same_image = current_image.tobytes() == inspiration_image.tobytes()
        except Exception:
            pass

    # Extract dynamic budget from prompt if present
    effective_budget, _, is_prompt_budget = extract_budget_from_prompt(user_prompt, budget)
    intents = detect_renovation_intents(user_prompt)

    special_directives = []
    if is_prompt_budget:
        special_directives.append(f"- USER-SPECIFIED BUDGET: The user explicitly specified '{effective_budget}' in their prompt. This MUST be the primary budget for all recommendations.")
    
    if intents["min_money_mode"]:
        special_directives.append("- MINIMUM MONEY PRIORITY: The user wants to spend as little as possible. Prioritize ultra-low-cost, high-impact changes (decluttering, cleaning, deep restoration, low-cost hardware) as the main priority.")
        
    if intents["rearrange_only_mode"] or intents["no_paint_mode"]:
        special_directives.append("- NO-PAINT / NO-CEILING CONSTRAINT: The user asked NOT to modify paint or ceilings. Identify existing elements that can be REPOSITIONED, REARRANGED, or STAGED to mimic the inspiration photo without altering surfaces.")

    if is_same_image:
        special_directives.append("""- IDENTICAL IMAGES PROVIDED: The user uploaded the same photo for current space and inspiration. Treat this as a 'FAITHFUL STYLE-PRESERVING REFRESH'. The user loves their current aesthetic; focus on cosmetic restoration and durability upgrades in the same color tones.""")

    directives_block = "\n".join(special_directives) if special_directives else "None"

    prompt = f"""
You are the VISUAL ASSESSOR, an expert architectural and interior design visual AI.

TASK:
Analyze the uploaded image(s) and user request for a {room_type} renovation with an active budget of {effective_budget}.

SPECIAL USER DIRECTIVES DETECTED:
{directives_block}

User's Notes / Request: "{user_prompt}"

DETECTION & ANALYSIS INSTRUCTIONS:
1. CURRENT ROOM PHOTO (if provided):
   - Assess current condition, wear, outdated elements, and lighting.
   - CRITICAL - DOCUMENT THE EXACT STRUCTURAL LAYOUT TO PRESERVE:
     * Window locations and dimensions
     * Door openings and pathways
     * Cabinet configurations (upper/lower, L-shaped, U-shaped, galley)
     * Major appliance / plumbing positions (sink, stove, refrigerator, dishwasher)
     * Countertop spans
     * Camera perspective/angle of the photograph
   - Highlight high-impact improvements.

2. INSPIRATION PHOTO (if provided):
   - Extract design aesthetic (e.g., Modern Farmhouse, Warm Minimalist, Japandi).
   - Identify color palette (specific shades, undertones).
   - Identify signature materials (stone types, wood grains, metal finishes).
   - Note decorative elements (lighting fixtures, backsplash patterns, hardware).

3. SAME-HOUSE OR MULTI-ANGLE DETECTION:
   - If Photo 2 appears to be ANOTHER ROOM IN THE SAME HOUSE (or an already-renovated adjacent space):
     * Emphasize WHOLE-HOME ARCHITECTURAL COHESION.
     * Ensure seamless flooring transitions at room thresholds (matching stain, grain, and floor height).
     * Coordinate millwork, door trim profiles, and baseboard styles.
     * Maintain a unified metal hardware language (e.g., consistent matte black or warm brass throughout).
   - If Photo 2 is a DIFFERENT ANGLE OF THE SAME ROOM:
     * Synthesize both angles into a comprehensive 3D spatial map of all walls, counters, windows, and appliances.

4. BUDGET EVALUATION:
   - Base scope evaluation strictly within {effective_budget}.

Provide a thorough, highly structured assessment report with markdown headings:
- 📸 Space Condition & Observations
- 🔒 Exact Structural Layout (Must be preserved in rendering)
- 🎨 Extracted Style & Material Direction
- 💡 High-Impact Renovation Opportunities
"""
    contents = [prompt]
    if current_image is not None:
        contents.append(image_to_part(current_image))
    if inspiration_image is not None:
        contents.append(image_to_part(inspiration_image))

    try:
        response = client.models.generate_content(model=model, contents=contents)
        return response.text
    except Exception as e:
        logger.warning(f"Failed with {model}, trying fallback: {e}")
        response = client.models.generate_content(model=FALLBACK_VISION_MODEL, contents=contents)
        return response.text


# ============================================================================
# Specialist 2: Design Planner Agent
# ============================================================================

def generate_design_plan(
    client: genai.Client,
    assessment_text: str,
    style_preference: str,
    room_type: str,
    budget: str,
    user_prompt: str = "",
    model: str = DEFAULT_VISION_MODEL,
) -> str:
    """Creates specific surface finish specifications maintaining exact layout, budget, and stretch tiers."""
    effective_budget, _, _ = extract_budget_from_prompt(user_prompt, budget)
    intents = detect_renovation_intents(user_prompt)

    # Specific directives for DesignPlanner
    design_rules = []
    if intents["no_paint_mode"] or intents["rearrange_only_mode"]:
        design_rules.append("""
**STRICT USER CONSTRAINT - NO PAINT & NO CEILING MODIFICATIONS:**
- DO NOT specify wall paint, cabinet paint, or ceiling changes!
- Focus 100% on **Spatial Realignment & Visual Staging**:
  * Move existing movable furniture, carts, chairs, or open shelf items to match the inspiration photo composition.
  * Countertop styling: declutter, rearrange appliances, and style with inspiration-matched cutting boards, canisters, and runners.
  * Non-destructive hardware swaps or lighting adjustments using existing junction boxes.
""")
    if intents["min_money_mode"]:
        design_rules.append("""
**STRICT USER CONSTRAINT - MINIMUM MONEY AS PRIMARY GOAL:**
- Primary recommendation MUST be the absolute minimum cost possible (Level 1: Shoestring / Sweat Equity).
- Suggest free/low-cost changes first (deep cleaning, hardware polishing, rearranging, minimal DIY).
""")

    rules_block = "\n".join(design_rules) if design_rules else ""

    prompt = f"""
You are the DESIGN PLANNER, an elite interior designer.

Based on the Visual Assessor's report below, create a SPECIFIC, ACTIONABLE design plan.

STRICT RULE - PRESERVE EXACT PHYSICAL LAYOUT:
- DO NOT suggest moving plumbing, knocking down walls, or moving appliances.
- ONLY specify upgrades to SURFACE FINISHES applied to the existing footprint (unless user requested no paint/staging only).

Target Room: {room_type}
Target Style: {style_preference}
Primary Budget Constraint: {effective_budget} (MUST BE RIGOROUSLY RESPECTED AS PRIMARY BASELINE)

{rules_block}

Visual Assessment Report:
\"\"\"{assessment_text}\"\"\"

SPECIFY PRECISE FINISHES:
1. Cabinet Finishes: Exact paint color with manufacturer/code (or existing finish if no-paint requested), finish sheen (Satin/Matte).
2. Countertops: Exact stone/material (e.g., Honed Carrara marble, Calacatta Gold quartz, butcher block), edge profile.
3. Backsplash: Tile material, shape, layout pattern (e.g., herringbone, stacked, subway), grout color.
4. Flooring: Material, width, stain/color (e.g., 7" wide-plank European white oak, satin finish).
5. Hardware: Pull/knob style, metal finish (e.g., brushed brass, matte black, polished nickel).
6. Lighting: Exact fixture styles (pendant, flush mount, under-cabinet LED temperature 2700K-3000K).
7. Wall & Trim Paint: Cohesive wall paint and trim colors with exact codes (or note existing if no-paint requested).
8. Decorative & Staging Elements: Arranging and staging items to mimic the inspiration aesthetic.

MANDATORY FINAL SECTION:
At the very end of your response, you MUST provide:
### 🚀 STRETCH BUDGET UPGRADE (WHAT A SMALL EXTRA INVESTMENT UNLOCKS)
- Explain: If the user can increase their budget by just a modest amount (e.g. +$1,000 to +$3,000), what are the 2-3 highest-leverage upgrades that will exponentially elevate the space?
- Detail the exact extra items (e.g., solid slab quartz vs laminate, professional cabinet lacquer spraying, hardwired under-cabinet LED channels).
- State why this small stretch provides disproportionately high visual and durability returns.

Format as a beautifully structured design specification sheet.
"""
    try:
        response = client.models.generate_content(model=model, contents=prompt)
        return response.text
    except Exception as e:
        response = client.models.generate_content(model=FALLBACK_VISION_MODEL, contents=prompt)
        return response.text


# ============================================================================
# Specialist 3: Project Coordinator & Roadmap
# ============================================================================

def generate_project_roadmap(
    client: genai.Client,
    assessment_text: str,
    design_plan_text: str,
    room_type: str,
    budget: str,
    user_prompt: str = "",
    model: str = DEFAULT_VISION_MODEL,
) -> Tuple[str, str]:
    """Generates budget breakdown, timeline, contractor checklist, stretch budget line items, and the photorealistic SLC prompt."""
    effective_budget, _, _ = extract_budget_from_prompt(user_prompt, budget)
    intents = detect_renovation_intents(user_prompt)

    prompt = f"""
You are the PROJECT COORDINATOR, an experienced general contractor and project manager.

Synthesize the assessment and design plan into an executive renovation roadmap and photorealistic rendering prompt.

Room: {room_type}
Primary Baseline Budget: {effective_budget} (MUST BE RIGOROUSLY RESPECTED FOR THE BASE PLAN)

Design Specifications:
\"\"\"{design_plan_text}\"\"\"

DELIVER TWO SECTIONS:

### SECTION 1: EXECUTION ROADMAP & BUDGET
- Line-Item Budget Breakdown (strictly fits within {effective_budget}):
  * Materials & Fixtures: $...
  * Labor & Trades: $...
  * Permits, Delivery & Waste: $...
  * Contingency (10%): $...
  * TOTAL ESTIMATED BASELINE COST: $...
- Stretch Budget Scenario (e.g., +$1,500 - $3,000 Upgrade Tier):
  * List the specific add-on costs and total stretched investment.
- Project Timeline: Total weeks broken down into sequential phases (Demo/Prep, Surface Installation, Finishes & Staging).
- Contractors / Trades Required: (e.g., Cabinet refinisher, Tile setter, Electrician, Plumber).
- Immediate 5-Step Action Checklist.

### SECTION 2: SLC PHOTOREALISTIC RENDERING BRIEF
Create an ultra-detailed, single-paragraph architectural photography prompt using the SLC formula (Subject, Lighting, Camera):
- CAMERA (C): Professional DSLR, 8K, HDR, wide-angle interior photography, sharp focus.
- SUBJECT (S): Exact renovated space with layout preserved, listing the specific colors, materials, countertop veins, flooring grain, and hardware chosen above.
- LIGHTING (L): Diffused natural morning sunlight, warm 3000K LED under-cabinet illumination, balanced ambient glow.
- Aesthetic keywords: Architectural Digest quality, magazine luxury interior, photorealistic.

Separate Section 1 and Section 2 clearly with the delimiter:
---SLC_PROMPT_START---
[Put the raw prompt paragraph here]
---SLC_PROMPT_END---
"""
    try:
        response = client.models.generate_content(model=model, contents=prompt)
        full_text = response.text
    except Exception as e:
        response = client.models.generate_content(model=FALLBACK_VISION_MODEL, contents=prompt)
        full_text = response.text

    slc_prompt = ""
    roadmap_text = full_text
    if "---SLC_PROMPT_START---" in full_text and "---SLC_PROMPT_END---" in full_text:
        parts = full_text.split("---SLC_PROMPT_START---")
        roadmap_text = parts[0].strip()
        slc_prompt = parts[1].split("---SLC_PROMPT_END---")[0].strip()
    else:
        slc_prompt = f"Professional 8K architectural photography of a renovated {room_type}, modern interior design, natural sunlight, luxury finishes."

    return roadmap_text, slc_prompt


# ============================================================================
# Specialist 4: Image Generation Engine
# ============================================================================

def try_generate_image(
    client: genai.Client,
    prompt: str,
    reference_image: Optional[Any] = None,
) -> Tuple[Optional[Image.Image], str]:
    """Attempts to generate image using Google GenAI image generation."""
    model_name = "gemini-3-pro-image-preview"
    try:
        parts = [types.Part.from_text(text=prompt)]
        if reference_image is not None:
            parts.append(image_to_part(reference_image))

        config = types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"]
        )
        
        response = client.models.generate_content(
            model=model_name,
            contents=[types.Content(role="user", parts=parts)],
            config=config,
        )

        for candidate in response.candidates:
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    if part.inline_data and part.inline_data.data:
                        img_bytes = part.inline_data.data
                        img = Image.open(io.BytesIO(img_bytes))
                        return img, "SUCCESS"

        return None, "No image bytes returned in model response."

    except Exception as e:
        err_msg = str(e)
        logger.info(f"Image generation attempted with {model_name}: {err_msg}")
        if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
            return None, "QUOTA_EXHAUSTED"
        elif "404" in err_msg or "NOT_FOUND" in err_msg:
            return None, "MODEL_NOT_FOUND"
        return None, f"ERROR: {err_msg}"


# ============================================================================
# Specialist 5: Iterative Refiner Agent
# ============================================================================

def refine_renovation_plan(
    client: genai.Client,
    current_design_plan: str,
    user_refinement: str,
    model: str = DEFAULT_VISION_MODEL,
) -> Tuple[str, str]:
    """Refines existing design specifications and updates the SLC rendering prompt."""
    intents = detect_renovation_intents(user_refinement)
    
    extra_instructions = ""
    if intents["min_money_mode"]:
        extra_instructions += "\n- USER REQUESTED MINIMUM COST: Suggest the lowest-spend adjustment first, then add optional step-up ideas."
    if intents["no_paint_mode"] or intents["rearrange_only_mode"]:
        extra_instructions += "\n- USER REQUESTED NO PAINT / REARRANGE ONLY: Do not change wall or cabinet paint. Tweak existing decor, furniture arrangement, or hardware only."

    prompt = f"""
You are the RENDERING & DESIGN REFINER.

The user wants to make a modification to their current renovation plan.
{extra_instructions}

CURRENT PLAN:
\"\"\"{current_design_plan}\"\"\"

USER'S REFINEMENT REQUEST:
\"{user_refinement}\"

INSTRUCTIONS:
1. Update the design specifications, modifying ONLY what the user requested.
2. Keep all unchanged elements exactly as specified.
3. If user requested minimal money, prioritize the cheapest solution first.
4. Keep the '🚀 STRETCH BUDGET UPGRADE' section updated.
5. Generate an updated, single-paragraph SLC photorealistic rendering prompt.

Format output as:
### REVISED DESIGN SPECIFICATIONS
[Updated finish changes]

---SLC_PROMPT_START---
[Updated 8K SLC architectural photography prompt]
---SLC_PROMPT_END---
"""
    try:
        response = client.models.generate_content(model=model, contents=prompt)
        text = response.text
    except Exception as e:
        response = client.models.generate_content(model=FALLBACK_VISION_MODEL, contents=prompt)
        text = response.text

    revised_plan = text
    new_slc_prompt = ""
    if "---SLC_PROMPT_START---" in text and "---SLC_PROMPT_END---" in text:
        parts = text.split("---SLC_PROMPT_START---")
        revised_plan = parts[0].strip()
        new_slc_prompt = parts[1].split("---SLC_PROMPT_END---")[0].strip()
    else:
        new_slc_prompt = f"Professional 8K architectural interior photo with modifications: {user_refinement}"

    return revised_plan, new_slc_prompt


# ============================================================================
# NEW FEATURE 1: Color Palette & Swatches Extractor
# ============================================================================

def extract_color_palette(
    client: genai.Client,
    design_plan_text: str,
    model: str = DEFAULT_VISION_MODEL,
) -> List[Dict[str, str]]:
    """Extracts 5 structured color swatches with HEX codes and finish types from the design plan."""
    prompt = f"""
From the interior design plan below, extract a cohesive 5-color palette representing the key finishes.
Return ONLY valid JSON array with objects containing:
- "name": Color/Material name (e.g. "Chantilly Lace", "Honed Carrara", "Natural White Oak", "Matte Black", "Warm Brass")
- "role": Application (e.g. "Cabinets", "Countertops", "Flooring", "Hardware / Accents", "Walls")
- "hex": Approximate 6-digit hex code starting with # (e.g. "#F4F6F0", "#E5E7EB", "#D4AF37", "#2C2C2C")
- "finish": Finish sheen (e.g. "Satin", "Honed", "Matte", "Brushed")

Design Plan:
\"\"\"{design_plan_text}\"\"\"

JSON output only, no surrounding text:
"""
    try:
        resp = client.models.generate_content(model=model, contents=prompt)
        clean_text = resp.text.strip()
        if clean_text.startswith("```"):
            clean_text = re.sub(r"^```(?:json)?\s*", "", clean_text)
            clean_text = re.sub(r"\s*```$", "", clean_text)
        data = json.loads(clean_text)
        if isinstance(data, list) and len(data) > 0:
            return data
    except Exception as e:
        logger.warning(f"Palette extraction fallback: {e}")
        
    return [
        {"name": "Benjamin Moore Simply White", "role": "Cabinets", "hex": "#F4F5F0", "finish": "Satin"},
        {"name": "Carrara Quartz", "role": "Countertops", "hex": "#E2E5E8", "finish": "Honed"},
        {"name": "European White Oak", "role": "Flooring", "hex": "#CBB296", "finish": "Matte Satin"},
        {"name": "Brushed Warm Brass", "role": "Hardware", "hex": "#D4AF37", "finish": "Brushed"},
        {"name": "Warm Linen Gray", "role": "Walls", "hex": "#DDD8CE", "finish": "Eggshell"},
    ]


# ============================================================================
# NEW FEATURE 2: DIY vs. Pro Feasibility & Cost Savings
# ============================================================================

def generate_diy_vs_pro(
    client: genai.Client,
    design_plan_text: str,
    room_type: str,
    budget: str,
    model: str = DEFAULT_VISION_MODEL,
) -> str:
    """Classifies tasks into DIY-friendly vs. hire-a-pro with potential labor savings."""
    prompt = f"""
You are a Renovation Cost & Labor Consultant.

Analyze this design plan for a {room_type} with a {budget} budget:
\"\"\"{design_plan_text}\"\"\"

Provide an actionable DIY vs. Pro breakdown with:
1. 🟢 DIY-Friendly Tasks (low risk, high sweat equity savings, e.g. cabinet painting, hardware installation, backsplash tiling, trim paint)
   - Estimated potential labor savings: $...
2. 🔴 Tasks Requiring Licensed Pros (high risk, code compliance, e.g. electrical rerouting, gas line work, countertop slab templating and installation)
   - Reason why a pro is critical.
3. 💡 Overall Potential DIY Savings Summary: (e.g. "By handling painting and hardware yourself, you can save approximately $1,500 - $3,000 in trade labor").
"""
    try:
        resp = client.models.generate_content(model=model, contents=prompt)
        return resp.text
    except Exception as e:
        resp = client.models.generate_content(model=FALLBACK_VISION_MODEL, contents=prompt)
        return resp.text


# ============================================================================
# NEW FEATURE 3: Material Quantity & Dimension Calculator
# ============================================================================

def calculate_material_quantities(
    length_ft: float,
    width_ft: float,
    ceiling_ft: float = 8.0,
    room_type: str = "Kitchen"
) -> Dict[str, Any]:
    """Calculates square footage, paint gallons, flooring boxes, and tile needs."""
    floor_sqft = length_ft * width_ft
    perimeter = 2 * (length_ft + width_ft)
    wall_sqft = perimeter * ceiling_ft
    
    effective_wall_sqft = wall_sqft * 0.85
    paint_gallons = round((effective_wall_sqft * 2) / 375, 1)
    flooring_needed_sqft = round(floor_sqft * 1.10, 1)
    flooring_boxes = int(flooring_needed_sqft // 22) + 1
    backsplash_sqft = round(perimeter * 0.5 * 1.5, 1) if "kitchen" in room_type.lower() else 0
    tile_needed_sqft = round(backsplash_sqft * 1.15, 1)
    
    return {
        "floor_sqft": round(floor_sqft, 1),
        "wall_sqft": round(wall_sqft, 1),
        "perimeter_linear_ft": round(perimeter, 1),
        "paint_gallons": max(1.0, paint_gallons),
        "flooring_needed_sqft": flooring_needed_sqft,
        "flooring_boxes": flooring_boxes,
        "backsplash_sqft": tile_needed_sqft,
    }


# ============================================================================
# NEW FEATURE 4: Resale Value & Home ROI Estimator
# ============================================================================

def estimate_home_roi(budget_val: float, room_type: str) -> Dict[str, Any]:
    """Estimates national average Return on Investment (ROI) and home equity gain."""
    roi_rates = {
        "kitchen": 0.78,
        "master bathroom": 0.68,
        "guest bathroom": 0.71,
        "living room": 0.62,
        "master bedroom": 0.58,
        "home office": 0.60,
    }
    
    key = room_type.lower().strip()
    rate = 0.65
    for k, r in roi_rates.items():
        if k in key:
            rate = r
            break
            
    estimated_added_value = round(budget_val * rate, 0)
    net_effective_cost = round(budget_val - estimated_added_value, 0)
    
    return {
        "roi_percentage": int(rate * 100),
        "estimated_value_added": f"${estimated_added_value:,.0f}",
        "net_effective_cost": f"${net_effective_cost:,.0f}",
    }


# ============================================================================
# NEW FEATURE 5: Ready-to-Send Contractor RFQ Generator
# ============================================================================

def generate_contractor_rfq(
    client: genai.Client,
    design_plan_text: str,
    roadmap_text: str,
    room_type: str,
    budget: str,
    model: str = DEFAULT_VISION_MODEL,
) -> str:
    """Generates a professional Request For Quotation (RFQ) ready to copy-paste to contractors."""
    prompt = f"""
You are a Construction Contract Specialist.

Generate a ready-to-send Request for Quotation (RFQ) email template for a homeowner to email local contractors for a {room_type} renovation.

Project Budget: {budget}

Design Specs:
\"\"\"{design_plan_text[:1200]}\"\"\"

Project Roadmap:
\"\"\"{roadmap_text[:1200]}\"\"\"

Create a professional, bulleted email draft including:
- Subject Line
- Project Summary & Scope of Work
- Strict Layout Preservation requirement (no structural or plumbing moves)
- Required Contractor Credentials (Licensed, Insured, Workman's Comp)
- Requested Bid Items (Labor estimate, timeline in writing, milestone payment structure, references)
- Bid Submission Deadline placeholder
"""
    try:
        resp = client.models.generate_content(model=model, contents=prompt)
        return resp.text
    except Exception as e:
        resp = client.models.generate_content(model=FALLBACK_VISION_MODEL, contents=prompt)
        return resp.text


# ============================================================================
# NEW FEATURE 6: Renovation Consultant AI Assistant
# ============================================================================

def ask_renovation_consultant(
    client: genai.Client,
    question: str,
    design_plan_text: str,
    room_type: str,
    model: str = DEFAULT_VISION_MODEL,
) -> str:
    """Answers specific technical renovation questions regarding prep, materials, or building codes."""
    prompt = f"""
You are a Master Builder & Architectural Consultant.

Answer the homeowner's specific question regarding their {room_type} renovation project:

Project Context:
\"\"\"{design_plan_text[:1500]}\"\"\"

User's Question:
\"{question}\"

Provide practical, contractor-grade guidance (prep steps, durability considerations, building code gotchas, cost efficiency tips). Keep response concise, structured, and friendly.
"""
    try:
        resp = client.models.generate_content(model=model, contents=prompt)
        return resp.text
    except Exception as e:
        resp = client.models.generate_content(model=FALLBACK_VISION_MODEL, contents=prompt)
        return resp.text
