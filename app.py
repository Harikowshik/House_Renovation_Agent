"""AI Home Renovation Planner - Streamlit Application

A multimodal multi-agent application built directly with Google GenAI SDK:
- Visual Assessor: Multimodal layout and condition analysis
- Design Planner: Exact finish, color, and material specifications
- Project Coordinator: Budget breakdown, timeline, contractor checklist, and 8K SLC photography prompt
- Color Palette Extractor: Live interactive color swatch cards & HEX codes
- Material Quantity Calculator: Square footage, paint gallons, flooring boxes with waste factor
- ROI & Home Resale Estimator: Estimated home equity gain and ROI percentage
- DIY vs. Pro Analyzer: Sweat equity feasibility and trade labor savings
- Contractor RFQ Generator: One-click email brief for licensed contractor bids
- Renovation Consultant: 24/7 builder Q&A for permits, prep & codes
- Iterative Refiner: Conversational feedback for instant design tweaks
"""

import os
import sys
from pathlib import Path
from PIL import Image
import streamlit as st
from dotenv import load_dotenv

# Load local environment
load_dotenv()

# Import GenAI engine functions
from renovation_engine import (
    get_genai_client,
    assess_room_and_inspiration,
    generate_design_plan,
    generate_project_roadmap,
    try_generate_image,
    refine_renovation_plan,
    extract_color_palette,
    generate_diy_vs_pro,
    calculate_material_quantities,
    estimate_home_roi,
    generate_contractor_rfq,
    ask_renovation_consultant,
    extract_budget_from_prompt,
    detect_renovation_intents,
    DEFAULT_VISION_MODEL,
)
from pdf_generator import build_renovation_pdf

# Page Configuration
st.set_page_config(
    page_title="AI Home Renovation Planner",
    page_icon="🏚️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for rich aesthetics
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }

    .main-header {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 24px 32px;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
    }
    
    .header-title {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #f8fafc, #93c5fd);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 6px;
    }

    .header-sub {
        font-size: 1.05rem;
        color: #94a3b8;
    }

    .metric-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 16px 20px;
        text-align: center;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(147, 197, 253, 0.4);
    }
    .metric-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #60a5fa;
        margin-top: 4px;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .swatch-card {
        background: rgba(30, 41, 59, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 12px;
        text-align: center;
        margin-bottom: 10px;
    }
    .swatch-color {
        height: 60px;
        border-radius: 8px;
        margin-bottom: 10px;
        border: 1px solid rgba(255, 255, 255, 0.15);
    }
    .swatch-name {
        font-weight: 600;
        font-size: 0.92rem;
        color: #f8fafc;
    }
    .swatch-role {
        font-size: 0.78rem;
        color: #94a3b8;
        margin-bottom: 2px;
    }
    .swatch-hex {
        font-family: monospace;
        font-size: 0.82rem;
        color: #60a5fa;
        background: rgba(0,0,0,0.3);
        padding: 2px 6px;
        border-radius: 4px;
        display: inline-block;
    }

    .agent-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(59, 130, 246, 0.15);
        color: #93c5fd;
        border: 1px solid rgba(59, 130, 246, 0.3);
        border-radius: 20px;
        padding: 6px 14px;
        font-size: 0.88rem;
        margin-bottom: 12px;
    }

    div.stButton > button:first-child {
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
</style>
""", unsafe_allow_html=True)

SAMPLE_DIR = Path(__file__).resolve().parent / "sample_inputs"

# Initialize Session State
if "current_image" not in st.session_state:
    st.session_state.current_image = None
if "inspiration_image" not in st.session_state:
    st.session_state.inspiration_image = None
if "curr_upload_key" not in st.session_state:
    st.session_state.curr_upload_key = 0
if "insp_upload_key" not in st.session_state:
    st.session_state.insp_upload_key = 0
if "assessment" not in st.session_state:
    st.session_state.assessment = None
if "design_plan" not in st.session_state:
    st.session_state.design_plan = None
if "roadmap" not in st.session_state:
    st.session_state.roadmap = None
if "slc_prompt" not in st.session_state:
    st.session_state.slc_prompt = None
if "rendered_image" not in st.session_state:
    st.session_state.rendered_image = None
if "image_status" not in st.session_state:
    st.session_state.image_status = None
if "color_palette" not in st.session_state:
    st.session_state.color_palette = None
if "diy_breakdown" not in st.session_state:
    st.session_state.diy_breakdown = None
if "rfq_text" not in st.session_state:
    st.session_state.rfq_text = None
if "custom_prompt" not in st.session_state:
    st.session_state.custom_prompt = ""
if "consultant_chat" not in st.session_state:
    st.session_state.consultant_chat = []


# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Settings & API Key")
    
    saved_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or ""
    api_key = st.text_input(
        "Google Gemini API Key",
        value=saved_key,
        type="password",
        help="Get your key from https://aistudio.google.com/",
    )
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
        st.success("API Key Active ✓", icon="🟢")
    else:
        st.warning("Please enter your Gemini API key", icon="⚠️")

    st.markdown("---")
    st.markdown("### 🛠️ Renovation Parameters")
    
    room_type = st.selectbox(
        "Room Type",
        ["Kitchen", "Master Bathroom", "Guest Bathroom", "Living Room", "Master Bedroom", "Home Office", "Dining Room"],
        index=0,
    )
    
    budget_raw = st.select_slider(
        "Budget Constraint",
        options=["$5,000", "$10,000", "$15,000", "$25,000", "$40,000", "$60,000", "$100,000+"],
        value="$15,000",
    )
    budget_num = float(budget_raw.replace("$", "").replace(",", "").replace("+", ""))
    
    target_style = st.selectbox(
        "Target Aesthetic",
        [
            "Modern Farmhouse",
            "Warm Minimalist",
            "Japandi",
            "Scandinavian",
            "Contemporary Luxury",
            "Industrial Loft",
            "Mid-Century Modern",
            "Transitional",
        ],
        index=0,
    )

    st.markdown("---")
    st.markdown("### 📐 Room Dimensions (Estimator)")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        dim_length = st.number_input("Length (ft)", min_value=4.0, max_value=60.0, value=12.0, step=0.5)
    with col_d2:
        dim_width = st.number_input("Width (ft)", min_value=4.0, max_value=60.0, value=10.0, step=0.5)
    dim_height = st.number_input("Ceiling Height (ft)", min_value=7.0, max_value=16.0, value=9.0, step=0.5)

    st.markdown("---")
    st.markdown("### ⚡ Quick-Load Samples")
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        if st.button("🍳 Kitchen", use_container_width=True):
            k_curr = SAMPLE_DIR / "outdated_kitchen.jpg"
            k_insp = SAMPLE_DIR / "kitchen_inspiration.jpg"
            st.session_state.curr_upload_key += 1
            st.session_state.insp_upload_key += 1
            if k_curr.exists():
                st.session_state.current_image = Image.open(k_curr)
            if k_insp.exists():
                st.session_state.inspiration_image = Image.open(k_insp)
            st.session_state.custom_prompt = "Renovate this outdated 1990s kitchen with honey oak cabinets into a modern farmhouse aesthetic. Preserve the exact layout!"
            st.rerun()

    with col_s2:
        if st.button("🛁 Bathroom", use_container_width=True):
            b_curr = SAMPLE_DIR / "outdated_bathroom.jpg"
            b_insp = SAMPLE_DIR / "bathroom_inspiration.jpg"
            st.session_state.curr_upload_key += 1
            st.session_state.insp_upload_key += 1
            if b_curr.exists():
                st.session_state.current_image = Image.open(b_curr)
            if b_insp.exists():
                st.session_state.inspiration_image = Image.open(b_insp)
            st.session_state.custom_prompt = "Transform this dated 1980s bathroom into a luxury spa retreat with fluted vanity and walk-in shower. Keep plumbing in place!"
            st.rerun()

    if st.button("🔄 Clear All", use_container_width=True):
        st.session_state.curr_upload_key += 1
        st.session_state.insp_upload_key += 1
        for k in ["current_image", "inspiration_image", "assessment", "design_plan", "roadmap", "slc_prompt", "rendered_image", "image_status", "color_palette", "diy_breakdown", "rfq_text", "consultant_chat"]:
            st.session_state[k] = None if k != "consultant_chat" else []
        st.session_state.custom_prompt = ""
        st.rerun()


# Main Application Header
st.markdown("""
<div class="main-header">
    <div class="header-title">🏚️ 🍌 AI Home Renovation Planner</div>
    <div class="header-sub">Complete multi-agent renovation intelligence: layout preservation, exact paint & finish specs, itemized budgets, ROI resale estimation, DIY savings, and contractor RFQ generation.</div>
</div>
""", unsafe_allow_html=True)


# Top Section: Image Uploaders
st.markdown("### 📸 Space & Inspiration Photos")
col_img1, col_img2 = st.columns(2)

with col_img1:
    st.markdown("**1. Current Space Photo (Required for visual analysis)**")
    curr_uploader_id = f"upload_curr_{st.session_state.curr_upload_key}"
    uploaded_curr = st.file_uploader("Upload Current Room", type=["jpg", "jpeg", "png"], key=curr_uploader_id)
    if uploaded_curr is not None:
        st.session_state.current_image = Image.open(uploaded_curr)
    
    if st.session_state.current_image is not None:
        st.image(st.session_state.current_image, caption="Current Space", use_container_width=True)
        if st.button("🗑️ Remove Current Photo", key="btn_rem_curr"):
            st.session_state.current_image = None
            st.session_state.curr_upload_key += 1
            st.rerun()
    else:
        st.info("Upload a photo of your existing room, or click '🍳 Kitchen' / '🛁 Bathroom' in the sidebar.")

with col_img2:
    st.markdown("**2. Inspiration Style Photo (Optional)**")
    insp_uploader_id = f"upload_insp_{st.session_state.insp_upload_key}"
    uploaded_insp = st.file_uploader("Upload Inspiration Image", type=["jpg", "jpeg", "png"], key=insp_uploader_id)
    if uploaded_insp is not None:
        st.session_state.inspiration_image = Image.open(uploaded_insp)
        
    if st.session_state.inspiration_image is not None:
        st.image(st.session_state.inspiration_image, caption="Target Inspiration", use_container_width=True)
        if st.button("🗑️ Remove Inspiration Photo", key="btn_rem_insp"):
            st.session_state.inspiration_image = None
            st.session_state.insp_upload_key += 1
            st.rerun()
    else:
        st.info("Optional: Upload a Pinterest or magazine photo showing your desired style.")

# Detect identical images
if st.session_state.current_image is not None and st.session_state.inspiration_image is not None:
    try:
        if st.session_state.current_image.tobytes() == st.session_state.inspiration_image.tobytes():
            st.info("✨ **Style-Preserving Refresh Mode**: You uploaded the same photo for both your space and inspiration! The agents will modernize finishes, repair wear and tear, and upgrade lighting while faithfully preserving your existing aesthetic.", icon="💡")
    except Exception:
        pass

st.markdown("---")

# User Prompt Box
user_prompt = st.text_area(
    "💬 What specific goals or priorities do you have for this project?",
    value=st.session_state.custom_prompt,
    placeholder="e.g., Update the cabinets, replace countertops with quartz, add warm lighting, and keep under $15k...",
    height=80,
)

# Live Intent & Budget Detection
effective_budget_str, effective_budget_num, is_from_prompt = extract_budget_from_prompt(user_prompt, budget_raw)
intents = detect_renovation_intents(user_prompt)

if is_from_prompt:
    st.success(f"🎯 **Budget Detected in Prompt**: **{effective_budget_str}** (Overriding sidebar selection '{budget_raw}' as primary constraint)", icon="💰")

if intents["min_money_mode"]:
    st.info("📉 **Minimum Cost Priority Active**: The agents will formulate the lowest-spend plan first, followed by optional high-ROI stretch upgrades.", icon="💡")

if intents["rearrange_only_mode"] or intents["no_paint_mode"]:
    st.info("🪑 **Zero-Paint & Staging Mode Active**: No wall or cabinet painting, no ceiling changes. Focusing exclusively on spatial realignment, furniture repositioning & accessory staging.", icon="🚫")

# Execution CTA
btn_generate = st.button("🚀 Run Multi-Agent Renovation Pipeline", type="primary", use_container_width=True)

if btn_generate:
    if not api_key:
        st.error("Please enter a valid Google Gemini API key in the sidebar to proceed.")
    else:
        try:
            client = get_genai_client(api_key)
            
            progress_box = st.container()
            with progress_box:
                p_bar = st.progress(0)
                status_text = st.empty()

                # Step 1: Visual Assessor
                status_text.markdown('<div class="agent-pill">📸 Visual Assessor Agent: Inspecting room layout, structure & boundaries...</div>', unsafe_allow_html=True)
                p_bar.progress(15)
                assessment = assess_room_and_inspiration(
                    client=client,
                    current_image=st.session_state.current_image,
                    inspiration_image=st.session_state.inspiration_image,
                    user_prompt=user_prompt,
                    room_type=room_type,
                    budget=effective_budget_str,
                )
                st.session_state.assessment = assessment
                p_bar.progress(35)

                # Step 2: Design Planner
                status_text.markdown('<div class="agent-pill">🎨 Design Planner Agent: Selecting exact paint codes, countertop stones & finishes...</div>', unsafe_allow_html=True)
                design_plan = generate_design_plan(
                    client=client,
                    assessment_text=assessment,
                    style_preference=target_style,
                    room_type=room_type,
                    budget=effective_budget_str,
                    user_prompt=user_prompt,
                )
                st.session_state.design_plan = design_plan
                p_bar.progress(55)

                # Step 3: Project Coordinator
                status_text.markdown('<div class="agent-pill">🏗️ Project Coordinator: Formulating budget breakdown, timeline & contractor checklist...</div>', unsafe_allow_html=True)
                roadmap, slc_prompt = generate_project_roadmap(
                    client=client,
                    assessment_text=assessment,
                    design_plan_text=design_plan,
                    room_type=room_type,
                    budget=effective_budget_str,
                    user_prompt=user_prompt,
                )
                st.session_state.roadmap = roadmap
                st.session_state.slc_prompt = slc_prompt
                p_bar.progress(70)

                # Step 4: Color Swatches Extraction
                status_text.markdown('<div class="agent-pill">🎨 Palette Specialist: Extracting live HEX swatches & material codes...</div>', unsafe_allow_html=True)
                palette = extract_color_palette(client=client, design_plan_text=design_plan)
                st.session_state.color_palette = palette
                p_bar.progress(80)

                # Step 5: DIY vs Pro Breakdown
                status_text.markdown('<div class="agent-pill">🛠️ Labor Consultant: Analyzing sweat equity & DIY savings...</div>', unsafe_allow_html=True)
                diy_data = generate_diy_vs_pro(client=client, design_plan_text=design_plan, room_type=room_type, budget=budget_raw)
                st.session_state.diy_breakdown = diy_data
                p_bar.progress(90)

                # Step 6: Rendering Engine
                status_text.markdown('<div class="agent-pill">📷 Visual Rendering Engine: Generating photorealistic render...</div>', unsafe_allow_html=True)
                rendered_img, img_status = try_generate_image(
                    client=client,
                    prompt=slc_prompt,
                    reference_image=st.session_state.current_image,
                )
                st.session_state.rendered_image = rendered_img
                st.session_state.image_status = img_status

                p_bar.progress(100)
                status_text.empty()
                p_bar.empty()

            st.success("✅ Complete Multi-Agent Renovation Plan & Analysis Ready!")
            st.rerun()

        except Exception as e:
            st.error(f"Error during renovation pipeline execution: {e}")


# Results Section
if st.session_state.assessment and st.session_state.design_plan and st.session_state.roadmap:
    st.markdown("## 📊 Renovation Project Dashboard")

    # High-level Metrics Row (Including ROI calculated from effective budget!)
    roi_info = estimate_home_roi(effective_budget_num, room_type)
    
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Active Budget</div>
            <div class="metric-value">{effective_budget_str}</div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Estimated Home Equity Gain</div>
            <div class="metric-value">+{roi_info['estimated_value_added']}</div>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Expected Resale ROI</div>
            <div class="metric-value">{roi_info['roi_percentage']}%</div>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Net Effective Cost</div>
            <div class="metric-value">{roi_info['net_effective_cost']}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Interactive Color Swatch Bar
    if st.session_state.color_palette:
        st.markdown("### 🎨 Curated Finish & Color Swatches")
        cols_sw = st.columns(len(st.session_state.color_palette))
        for idx, swatch in enumerate(st.session_state.color_palette):
            with cols_sw[idx]:
                st.markdown(f"""
                <div class="swatch-card">
                    <div class="swatch-color" style="background-color: {swatch.get('hex', '#E2E8F0')};"></div>
                    <div class="swatch-role">{swatch.get('role', 'Accent')}</div>
                    <div class="swatch-name">{swatch.get('name', 'Finish')}</div>
                    <span class="swatch-hex">{swatch.get('hex', '#FFFFFF')}</span>
                    <div style="font-size: 0.75rem; color: #cbd5e1; margin-top: 4px;">{swatch.get('finish', 'Matte')}</div>
                </div>
                """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    # Visual Comparison (Before / Inspiration / Render)
    st.markdown("### 🖼️ Visual Comparison")
    c_v1, c_v2 = st.columns(2)
    with c_v1:
        if st.session_state.current_image:
            st.image(st.session_state.current_image, caption="Before (Current Space)", use_container_width=True)
    with c_v2:
        if st.session_state.rendered_image is not None:
            st.image(st.session_state.rendered_image, caption="After (Photorealistic AI Rendering)", use_container_width=True)
        elif st.session_state.inspiration_image is not None:
            st.image(st.session_state.inspiration_image, caption="Target Inspiration Aesthetic", use_container_width=True)
        else:
            st.info("Upload an inspiration photo to preview alongside your current space.")

    if st.session_state.image_status == "QUOTA_EXHAUSTED":
        st.info("""
        💡 **Image Generation Notice**: Google AI Studio provides free quota for text and multimodal vision analysis. Direct image generation models (`gemini-3-pro-image`) require Pay-As-You-Go billing in Google AI Studio. You can copy the generated prompt below to render in Midjourney or Imagen anytime!
        """)

    st.markdown("<br>", unsafe_allow_html=True)

    # Tabbed Detailed Features
    tab_road, tab_design, tab_quant, tab_diy, tab_rfq, tab_chat, tab_prompt = st.tabs([
        "📋 Budget & Roadmap",
        "🎨 Design Specifications",
        "📐 Material Quantities",
        "🛠️ DIY vs. Pro Feasibility",
        "📄 Contractor RFQ Email",
        "💬 Builder Q&A & Refiner",
        "📷 8K Rendering Prompt",
    ])

    with tab_road:
        st.markdown(st.session_state.roadmap)

    with tab_design:
        st.markdown(st.session_state.design_plan)

    with tab_quant:
        st.markdown("#### 📐 Estimated Material Quantities (Based on Room Dimensions)")
        quantities = calculate_material_quantities(dim_length, dim_width, dim_height, room_type)
        
        q1, q2, q3, q4 = st.columns(4)
        with q1:
            st.metric("Total Floor Area", f"{quantities['floor_sqft']} sq ft")
        with q2:
            st.metric("Paint Needed (2 coats)", f"{quantities['paint_gallons']} Gallons")
        with q3:
            st.metric("Flooring (+10% waste)", f"{quantities['flooring_needed_sqft']} sq ft", f"~{quantities['flooring_boxes']} Boxes")
        with q4:
            if quantities['backsplash_sqft'] > 0:
                st.metric("Tile Needed (+15% waste)", f"{quantities['backsplash_sqft']} sq ft")
            else:
                st.metric("Wall Perimeter", f"{quantities['perimeter_linear_ft']} Linear ft")

        st.caption("Calculated from room dimensions specified in the sidebar with standard industry waste factors.")

    with tab_diy:
        st.markdown("#### 🛠️ Sweat Equity & Trade Labor Analysis")
        if st.session_state.diy_breakdown:
            st.markdown(st.session_state.diy_breakdown)
        else:
            st.info("Generate the plan to view DIY savings breakdown.")

    with tab_rfq:
        st.markdown("#### 📄 Ready-to-Send Contractor Request for Quotation (RFQ)")
        st.write("Copy and paste this professional project brief directly into an email to send to local licensed contractors:")
        
        if not st.session_state.rfq_text:
            if st.button("Generate Contractor RFQ Email Draft"):
                client = get_genai_client(api_key)
                st.session_state.rfq_text = generate_contractor_rfq(
                    client=client,
                    design_plan_text=st.session_state.design_plan,
                    roadmap_text=st.session_state.roadmap,
                    room_type=room_type,
                    budget=budget_raw,
                )
                st.rerun()
        else:
            st.text_area("Contractor Email Draft", value=st.session_state.rfq_text, height=350)
            if st.button("Regenerate RFQ Draft"):
                st.session_state.rfq_text = None
                st.rerun()

    with tab_chat:
        st.markdown("#### 💬 24/7 AI Renovation Consultant & Refiner")
        st.write("Ask any practical remodeling question (permits, cabinet prep, tile underlayment) or request design tweaks:")

        for q, a in st.session_state.consultant_chat:
            with st.chat_message("user"):
                st.write(q)
            with st.chat_message("assistant"):
                st.write(a)

        chat_input = st.text_input("Ask a question or request a design tweak:", placeholder="e.g. Can I paint over oak cabinets without sanding to bare wood? OR Make cabinets dark green.")
        if st.button("Submit to Consultant", key="btn_consultant"):
            if chat_input:
                client = get_genai_client(api_key)
                with st.spinner("Consulting master builder..."):
                    # Check if it's a tweak or a question
                    if any(w in chat_input.lower() for w in ["make", "change", "switch", "tweak", "replace", "color"]):
                        new_plan, new_slc = refine_renovation_plan(
                            client=client,
                            current_design_plan=st.session_state.design_plan,
                            user_refinement=chat_input,
                        )
                        st.session_state.design_plan = new_plan
                        st.session_state.slc_prompt = new_slc
                        # Also refresh swatches
                        st.session_state.color_palette = extract_color_palette(client=client, design_plan_text=new_plan)
                        ans = f"✅ I've updated the design specifications and color palette with your request: '{chat_input}'. Check the 'Design Specifications' tab to see the revised finishes!"
                    else:
                        ans = ask_renovation_consultant(
                            client=client,
                            question=chat_input,
                            design_plan_text=st.session_state.design_plan,
                            room_type=room_type,
                        )
                    st.session_state.consultant_chat.append((chat_input, ans))
                    st.rerun()

    with tab_prompt:
        st.markdown("#### Architectural Photography Prompt (Subject, Lighting, Camera Formula)")
        st.markdown("This prompt is engineered to generate professional magazine-grade interior photography while keeping the exact layout of your space:")
        st.code(st.session_state.slc_prompt, language="text")

    # Download Reports (Both PDF and Markdown)
    st.markdown("---")
    st.markdown("### 📥 Export Your Renovation Dossier")

    full_report = f"""# AI Home Renovation Plan
**Room Type**: {room_type}
**Budget**: {effective_budget_str}
**Target Style**: {target_style}
**Estimated Resale Value Added**: {roi_info['estimated_value_added']} ({roi_info['roi_percentage']}% ROI)

---
## 1. Visual Assessment
{st.session_state.assessment}

---
## 2. Design Specifications
{st.session_state.design_plan}

---
## 3. Project Roadmap & Budget
{st.session_state.roadmap}

---
## 4. DIY vs. Pro Feasibility
{st.session_state.diy_breakdown}

---
## 5. SLC Photorealistic Rendering Prompt
{st.session_state.slc_prompt}
"""

    col_dl1, col_dl2 = st.columns(2)

    # 1. PDF Download
    with col_dl1:
        quantities_data = calculate_material_quantities(dim_length, dim_width, dim_height, room_type)
        try:
            import importlib
            import pdf_generator
            importlib.reload(pdf_generator)
            pdf_bytes = pdf_generator.build_renovation_pdf(
                room_type=room_type,
                budget=effective_budget_str,
                target_style=target_style,
                roi_info=roi_info,
                quantities=quantities_data,
                assessment=st.session_state.assessment or "",
                design_plan=st.session_state.design_plan or "",
                roadmap=st.session_state.roadmap or "",
                diy_breakdown=st.session_state.diy_breakdown or "",
                slc_prompt=st.session_state.slc_prompt or "",
            )
            st.download_button(
                label="📄 Download Print-Ready Dossier (.pdf)",
                data=pdf_bytes,
                file_name=f"{room_type.lower()}_renovation_dossier.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as e:
            import traceback
            traceback.print_exc()
            st.error(f"Error generating PDF: {e}")

    # 2. Markdown Download
    with col_dl2:
        st.download_button(
            label="📝 Download Complete Dossier (.md)",
            data=full_report,
            file_name=f"{room_type.lower()}_renovation_dossier.md",
            mime="text/markdown",
            use_container_width=True,
        )
