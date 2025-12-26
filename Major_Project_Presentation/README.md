# Flood Disaster Simulator

This repository contains a simple Flood Disaster Simulation demo with a Flask backend (implemented in `backend.ipynb`) and a Streamlit frontend (`app.py`). The backend uses lightweight image-processing heuristics (NDWI + noise) plus optional ML model hooks for experiments.

Contents

- `backend.ipynb` — Flask backend (notebook) that serves three endpoints: `/fetch_before`, `/simulate`, `/compare`.
- `app.py` — Streamlit frontend that uses Folium for geographic selection, uploads, and visual comparison.

Important notes

- This project includes placeholders for sensitive tokens: **Hugging Face token** (`HF_TOKEN`) and **ngrok token** (`NGROK_TOKEN`).
- The notebook loads several large ML models (CLIP, SegFormer, BLIP, Stable Diffusion). Expect long startup times and high RAM/VRAM usage. If you do not have a GPU, disable or skip heavy models (see "Optional: reduce memory" below).

Recommended environment (Windows PowerShell)

1. Install Python 3.10+.
2. Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Install basic Python dependencies (adjust for CPU/GPU PyTorch):

```powershell
pip install flask flask-cors pillow requests numpy opencv-python-headless pyngrok scikit-image perlin-noise
pip install transformers diffusers accelerate timm
# Streamlit frontend packages
pip install streamlit streamlit-folium folium streamlit-image-comparison
```

Notes on PyTorch: install a PyTorch wheel appropriate to your CUDA version or the CPU-only build. See https://pytorch.org/get-started/locally/ for the correct `pip` command. Example (CPU-only):

```powershell
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

How to run the backend
Option A — Run locally from the notebook (recommended for easy reproducibility):

- Open `backend.ipynb` with Jupyter or JupyterLab and run the cells top-to-bottom.
- Before running, set the tokens in the notebook or in PowerShell environment variables:

```powershell
$env:HF_TOKEN = "YOUR_HUGGING_FACE_TOKEN"
$env:NGROK_TOKEN = "YOUR_NGROK_TOKEN"
```

- The notebook contains a call to `ngrok.connect(5000)` which will produce a public URL. Copy that URL and set it into the frontend `app.py` `BACKEND_URL` or run the Streamlit front-end and enter the URL where prompted.

Option B — Convert the notebook to a script and run as Python script:

```powershell
# convert the notebook to a .py script
jupyter nbconvert --to script backend.ipynb --output backend
# run the generated script (may need minor edits if conversion adds cell-magic commands)
python backend.py
```

If you choose this route, ensure the top-of-script pip installs are either removed or executed manually; also make sure environment tokens are set before running.

How to run the frontend (Streamlit)

1. Edit `app.py` and set `BACKEND_URL` to the ngrok public URL printed by the backend, or to `http://127.0.0.1:5000` if running backend locally.
2. Run Streamlit:

```powershell
.\.venv\Scripts\Activate.ps1
streamlit run app.py
```

Security & tokens

- Keep `HF_TOKEN` and `NGROK_TOKEN` secret. Use environment variables instead of hardcoding them.
- Do not publish your ngrok token or Hugging Face token in public repos.

Optional: reduce memory / skip heavy models

- The notebook attempts to load multiple models. If you don't need them, comment out or guard the model-loading cells (e.g., skip loading `sd_pipe` or BLIP) to reduce memory usage.
- To avoid loading Stable Diffusion inpainting, set `sd_pipe = None` and skip its block.
- To avoid GPT/BLIP, set `gpt_model`, `blip_model` to `None` early.

Troubleshooting

- If `requests.get` to Google tile servers times out, check network/firewall or increase the `timeout` parameter.
- If the notebook fails due to missing CUDA, install CPU-only PyTorch or use a machine with a GPU.
- If Streamlit shows old backend, ensure `BACKEND_URL` matches the ngrok `public_url` logged by the backend.

Development suggestions

- Add a `requirements.txt` to pin versions for reproducibility.
- Add a small `backend.py` wrapper (a cleaned version of `backend.ipynb`) for easier local runs.
- Add logging and a health-check endpoint (`/health`) for the backend.

Example quick-start (PowerShell)

```powershell
# create & activate venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1
# install minimal deps (adjust for PyTorch as needed)
pip install flask flask-cors pillow requests numpy opencv-python-headless pyngrok scikit-image perlin-noise
pip install streamlit streamlit-folium folium streamlit-image-comparison
# set tokens
$env:HF_TOKEN = "YOUR_HF_TOKEN"
$env:NGROK_TOKEN = "YOUR_NGROK_TOKEN"
# run backend (open notebook and run cells) or run converted script
jupyter notebook backend.ipynb
# in another shell, run frontend
streamlit run app.py
```
