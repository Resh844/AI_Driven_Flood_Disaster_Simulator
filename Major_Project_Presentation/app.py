# app_frontend.py

import streamlit as st
from streamlit_folium import st_folium
import folium
from folium.plugins import Draw
from streamlit_image_comparison import image_comparison
from PIL import Image, ImageDraw, ImageFont
import io, requests, json, pandas as pd

# ------------------ BACKEND CONFIG ------------------
BACKEND_URL = "ADD the backend url by running hte backend code in collab(use NGROK for connecting)"
ENDPOINTS = {
    "fetch": f"{BACKEND_URL.rstrip('/')}/fetch_before",
    "simulate": f"{BACKEND_URL.rstrip('/')}/simulate",
    "compare": f"{BACKEND_URL.rstrip('/')}/compare"
}

# ------------------ PAGE CONFIG ------------------
st.set_page_config(
    page_title="Flood Disasater Simulator | Simulation",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------ DARK PREMIUM UI THEME ------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* GLOBAL DARK BACKGROUND */
html, body, [class*="css"] {
    background: #0d1117 !important;
    color: #e2e8f0 !important;
    font-family: 'Inter', sans-serif;
}

/* ------------------ SIDEBAR ------------------ */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #111827, #0f172a) !important;
    color: #e2e8f0 !important;
    border-right: 1px solid #1e293b !important;
}

[data-testid="stSidebar"] h2 {
    color: #60a5fa !important;
    font-weight: 700 !important;
}

/* Sidebar upload box */
[data-testid="stFileUploader"] section {
    background-color: #1e293b !important;
    border: 1px dashed #334155 !important;
    border-radius: 8px;
    padding: 0.7rem;
}
[data-testid="stFileUploader"] label {
    color: #cbd5e1 !important;
}

/* Text Input */
.stTextInput input {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    color: #f1f5f9 !important;
    border-radius: 8px;
}

/* ------------------ BUTTONS ------------------ */
.stButton > button {
    width: 100%;
    height: 3rem;
    border-radius: 8px;
    font-weight: 600;
    background: linear-gradient(90deg, #2563eb, #3b82f6) !important;
    color: white !important;
    border: none !important;
    transition: 0.2s ease-in-out;
}
.stButton > button:hover {
    transform: translateY(-3px);
    box-shadow: 0 6px 20px rgba(37, 99, 235, 0.35);
}

/* Secondary Button (Validation) */
[data-testid="stSidebar"] .stButton > button:nth-of-type(2) {
    background: transparent !important;
    border: 1px solid #334155 !important;
    color: #60a5fa !important;
}
[data-testid="stSidebar"] .stButton > button:nth-of-type(2):hover {
    background: #1e293b !important;
}

/* ------------------ HEADERS ------------------ */
.app-header {
    font-size: 2rem;
    font-weight: 700;
    color: #f8fafc;
}
.app-description {
    color: #94a3b8;
    margin-bottom: 1.5rem;
}

/* ------------------ METRICS ------------------ */
.metric-box {
    background: linear-gradient(180deg, rgba(37,99,235,0.14), rgba(59,130,246,0.06));
    border-radius: 12px;
    padding: 12px 14px;
    text-align: center;
    border: 1px solid rgba(59,130,246,0.08);
}
.metric-label { color:#cfe3ff; font-size:13px; font-weight:600; }
.metric-value { color:#ffffff; font-size:20px; font-weight:800; margin-top:6px; }

/* ------------------ CARDS / BLOCKS ------------------ */
.stTabs [data-baseweb="tab-list"] {
    background: #111827 !important;
    color: white !important;
}

.stTabs [data-baseweb="tab"] {
    background: #1e293b !important;
    padding: 8px 16px !important;
    border-radius: 6px !important;
    margin-right: 8px;
    color: #cbd5e1 !important;
}
.stTabs [aria-selected="true"] {
    background: #2563eb !important;
    color: white !important;
}

/* Table Styling */
.stDataFrame {
    background: #111827 !important;
}

/* Footer */
.footer-container {
    padding: 18px;
    border-radius: 10px;
    background: #1e293b;
    border: 1px solid #334155;
    color: #94a3b8;
    font-size: 0.85rem;
}

code {
    background: #1e293b !important;
    color: #60a5fa !important;
    padding: 3px 5px;
    border-radius: 4px;
}
</style>
""", unsafe_allow_html=True)

# ------------------ UTILITY ------------------
def annotate_hotspots(img, hotspots):
    img = img.copy().convert("RGBA")
    draw = ImageDraw.Draw(img, "RGBA")
    # attempt font
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 12)
    except:
        font = ImageFont.load_default()
    for h in hotspots:
        try:
            x, y = int(h.get("x", 0)), int(h.get("y", 0))
        except:
            continue
        sev = h.get("severity", "low")
        colors = {
            "high":    {"fill": (255, 80, 80, 140),  "outline": (255, 30, 30, 255), "r": 12},
            "medium":  {"fill": (255, 180, 60, 120), "outline": (255, 140, 0, 255), "r": 9},
            "low":     {"fill": (80, 150, 255, 110), "outline": (40, 110, 230, 255), "r": 7}
        }
        c = colors.get(sev, colors["low"])
        r = c["r"]
        draw.ellipse((x-r, y-r, x+r, y+r), fill=c["fill"], outline=c["outline"], width=2)
        draw.text((x + r + 4, y - r), sev[0].upper(), fill=(255,255,255,220), font=font)
    return img

def get_drawn_center(map_data):
    """
    Robustly parse st_folium output and extract the center (lat, lon)
    from the most recent rectangle drawing.
    """
    try:
        if not map_data:
            return None, None
        drawings = map_data.get("all_drawings") or map_data.get("drawn_objects") or map_data.get("last_active_drawing") or []
        # normalize to list of drawings
        if isinstance(drawings, dict):
            geom = drawings.get("geometry") or drawings
            coords = geom["coordinates"][0]
        elif isinstance(drawings, list) and len(drawings) > 0:
            # each item might be { "geometry": {...} } or geometry directly
            last = drawings[-1]
            geom = last.get("geometry", last) if isinstance(last, dict) else last
            coords = geom["coordinates"][0]
        else:
            return None, None
        lons = [p[0] for p in coords]; lats = [p[1] for p in coords]
        return ((min(lats) + max(lats))/2, (min(lons) + max(lons))/2)
    except Exception:
        return None, None

# ------------------ SIDEBAR CONTROLS ------------------
with st.sidebar:
    st.markdown("<h2>Flood Disasater Simulator using Stable Diffusion</h2>", unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Pre-disaster Baseline", type=["png","jpg","jpeg"])

    prompt = st.text_input("Simulation Prompt", placeholder="e.g., muddy flooding")

    real_post = st.file_uploader("Ground Truth (Optional)", type=["png","jpg","jpeg"])

    st.markdown("<br>", unsafe_allow_html=True)
    run_sim = st.button("🚀 Run Simulation")
    run_val = st.button("🔬 Validate Accuracy")

    st.markdown("---")
    st.caption(f"Backend: {BACKEND_URL}")

# ------------------ MAIN UI ------------------
st.markdown("<div class='app-header'>Flood Simulation Engine</div>", unsafe_allow_html=True)
st.markdown("<div class='app-description'>AI-powered geospatial flood modelling with hotspot detection.</div>", unsafe_allow_html=True)

tab_map, tab_results = st.tabs(["🌍 Geographic Selection", "📊 Simulation Analytics"])

# Keep a reference to map_data to be used by simulation logic.
map_data = None

# ------------------ MAP TAB ------------------
with tab_map:
    m = folium.Map(location=[20.59, 78.96], zoom_start=5, tiles=None)
    folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
        attr="© Google Maps",
        name="Satellite"
    ).add_to(m)
    Draw(export=True).add_to(m)

    # capture map_data returned by st_folium — needed later for drawn rectangle
    map_data = st_folium(m, height=600, width="100%")

# ------------------ SIMULATION LOGIC (INTEGRATED ORIGINAL) ------------------
if run_sim:
    # Prepare request: uploaded_file takes precedence over map rectangle
    try:
        files = None
        data = {}

        if uploaded_file:
            # file_uploader returns an UploadedFile; read bytes
            b = uploaded_file.read()
            files = {'file': ('input.png', b, 'image/png')}
        else:
            # get lat/lon from drawn rectangle on map
            lat, lon = get_drawn_center(map_data)
            if lat is None or lon is None:
                st.error("Please draw a rectangle on the map or upload a pre-disaster image.")
                st.stop()
            data['lat'] = str(lat); data['lon'] = str(lon)

        if prompt:
            data['prompt'] = prompt

        with st.spinner("🤖 Running simulation on backend..."):
            resp = requests.post(ENDPOINTS['simulate'], data=data, files=files, timeout=240)

        if resp.status_code != 200:
            st.error(f"Backend error: {resp.status_code} — {resp.text}")
        else:
            # Before image: from uploaded file or fetch from backend
            if uploaded_file:
                before_img = Image.open(io.BytesIO(b)).convert("RGB").resize((512,512))
            else:
                bf = requests.get(ENDPOINTS['fetch'], params={'lat': data['lat'], 'lon': data['lon']}, timeout=60)
                if bf.status_code == 200:
                    before_img = Image.open(io.BytesIO(bf.content)).convert("RGB").resize((512,512))
                else:
                    before_img = Image.new("RGB", (512,512), (230,230,230))

            # After image is response content
            after_img = Image.open(io.BytesIO(resp.content)).convert("RGB").resize((512,512))

            # Parse headers for metrics/hotspots (robust)
            metrics = {}
            hotspots = []
            x_metrics = resp.headers.get("X-Metrics")
            x_hotspots = resp.headers.get("X-Hotspots")
            if x_metrics:
                try:
                    metrics = json.loads(x_metrics)
                except:
                    try:
                        metrics = eval(x_metrics)
                    except:
                        metrics = {}
            if x_hotspots:
                try:
                    hotspots = json.loads(x_hotspots)
                except:
                    try:
                        hotspots = eval(x_hotspots)
                    except:
                        hotspots = []

            # annotate hotspots
            annotated = annotate_hotspots(after_img, hotspots)

            # save to session for compare
            st.session_state['before'] = before_img
            st.session_state['after'] = annotated
            st.session_state['metrics'] = metrics
            st.session_state['hotspots'] = hotspots

            st.success("✅ Simulation complete")

    except requests.exceptions.ReadTimeout:
        st.error("⏱️ Backend timed out. Try again or increase backend timeout.")
    except Exception as e:
        st.error(f"Simulation failed: {e}")

# ------------------ RESULTS TAB ------------------
with tab_results:
    if 'after' in st.session_state:
        # Prominent metric boxes
        m = st.session_state.get('metrics', {})
        c1, c2, c3, c4 = st.columns([1.2,1.2,1.2,1])
        c1.markdown(f"<div class='metric-box'><div class='metric-label'>SSIM</div><div class='metric-value'>{m.get('ssim','N/A')}</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-box'><div class='metric-label'>FID</div><div class='metric-value'>{m.get('fid','N/A')}</div></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='metric-box'><div class='metric-label'>Flood %</div><div class='metric-value'>{m.get('flood_percent','N/A')}%</div></div>", unsafe_allow_html=True)
        c4.markdown(f"<div style='text-align:center; color:#cbd5e1; font-size:14px;'><b>Hotspots:</b><br/>{len(st.session_state.get('hotspots',[]))}</div>", unsafe_allow_html=True)

        st.divider()

        # Visuals & table
        left, right = st.columns([2,1])
        with left:
            st.markdown("### Visual Comparison")
            image_comparison(img1=st.session_state['before'], img2=st.session_state['after'], label1="Before", label2="After (annotated)", width=800)
        with right:
            st.markdown("### Hotspot Dataset")
            df = pd.DataFrame(st.session_state.get('hotspots', []))
            if df.empty:
                st.write("No hotspots detected.")
            else:
                st.dataframe(df, use_container_width=True)
            # allow download
            if not df.empty:
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("⬇️ Download Hotspots CSV", csv, file_name="hotspots.csv", mime="text/csv")
    else:
        st.info("Run a simulation first from the Geographic Selection tab.")

# ------------------ VALIDATION / COMPARE (sidebar button triggered) ------------------
if run_val:
    # Validate accuracy by comparing st.session_state['after'] with uploaded real_post
    if 'after' not in st.session_state:
        st.error("Run simulation first (to produce a generated image).")
    elif real_post is None:
        st.error("Upload a ground-truth (post-disaster) image in the sidebar to validate.")
    else:
        try:
            # prepare files
            gen_buf = io.BytesIO()
            st.session_state['after'].save(gen_buf, format='PNG')
            gen_buf.seek(0)
            files = {
                'generated': ('generated.png', gen_buf.read(), 'image/png'),
                'real': ('real.png', real_post.read(), 'image/png')
            }
            with st.spinner("🔬 Comparing generated to real on backend..."):
                r = requests.post(ENDPOINTS['compare'], files=files, timeout=240)
            if r.status_code != 200:
                st.error(f"Backend compare failed: {r.status_code} → {r.text}")
            else:
                res = r.json()
                # show comparison metrics
                st.markdown("<div class='metric-box' style='display:flex; gap:12px; align-items:center; padding:10px;'>", unsafe_allow_html=True)
                st.markdown(f"<div style='flex:1; text-align:center;'><div class='metric-label'>Accuracy</div><div class='metric-value'>{res.get('accuracy',0):.2f}%</div></div>", unsafe_allow_html=True)
                st.markdown(f"<div style='flex:1; text-align:center;'><div class='metric-label'>Precision</div><div class='metric-value'>{res.get('precision',0):.3f}</div></div>", unsafe_allow_html=True)
                st.markdown(f"<div style='flex:1; text-align:center;'><div class='metric-label'>Recall</div><div class='metric-value'>{res.get('recall',0):.3f}</div></div>", unsafe_allow_html=True)
                st.markdown(f"<div style='flex:1; text-align:center;'><div class='metric-label'>F1</div><div class='metric-value'>{res.get('f1',0):.3f}</div></div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

                st.markdown(f"<div style='margin-top:8px; color:#cbd5e1;'>SSIM: {res.get('ssim','N/A')} &nbsp;&nbsp; FID: {res.get('fid','N/A')}</div>", unsafe_allow_html=True)

                # show images side-by-side
                real_img = Image.open(io.BytesIO(files['real'][1])).convert("RGB").resize((512,512))
                st.markdown("<div style='margin-top:12px'>", unsafe_allow_html=True)
                image_comparison(img1=st.session_state['after'], img2=real_img, label1="Generated (annotated)", label2="Real (post-disaster)")
                st.markdown("</div>", unsafe_allow_html=True)

        except requests.exceptions.ReadTimeout:
            st.error("⏱️ Backend compare request timed out.")
        except Exception as e:
            st.error(f"Compare failed: {e}")

# ------------------ FOOTER ------------------
st.markdown(f"""
<div class='footer-container'>
    • Keep Google Maps attribution if published.<br>
    • Backend must support <code>/fetch_before</code>, <code>/simulate</code>, <code>/compare</code>.<br>
    • Connected to backend: <code>{BACKEND_URL}</code>.
</div>
""", unsafe_allow_html=True)
