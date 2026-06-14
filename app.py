"""
🌿 GreenChem Score — Aplicación Streamlit
Pipeline ETL para clasificación química sostenible con visualizaciones interactivas.
"""

import streamlit as st
import pandas as pd
import sqlite3
import requests
import time
import re
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
from bs4 import BeautifulSoup
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import folium
from streamlit_folium import st_folium
import io
import base64

# ── Configuración de la página ─────────────────────────────────────────
st.set_page_config(
    page_title="GreenChem Score",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS personalizado ────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 800;
        color: #2E7D32;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #555;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
        border-radius: 15px;
        padding: 1.5rem;
        border-left: 5px solid #2E7D32;
    }
    .danger-card {
        background: linear-gradient(135deg, #FFEBEE 0%, #FFCDD2 100%);
        border-radius: 15px;
        padding: 1.5rem;
        border-left: 5px solid #C62828;
    }
    .warning-card {
        background: linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%);
        border-radius: 15px;
        padding: 1.5rem;
        border-left: 5px solid #EF6C00;
    }
    .stButton>button {
        background-color: #2E7D32;
        color: white;
        border-radius: 10px;
        padding: 0.5rem 2rem;
        font-weight: 600;
    }
    .stButton>button:hover {
        background-color: #1B5E20;
    }
    .footer {
        text-align: center;
        color: #888;
        font-size: 0.85rem;
        margin-top: 3rem;
        padding-top: 1rem;
        border-top: 1px solid #ddd;
    }
</style>
""", unsafe_allow_html=True)

# ── Constantes Globales ──────────────────────────────────────────────────
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

COURTESY_DELAY = 1.5
PUG_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
PUG_VIEW_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound"
OUTPUT_CSV = "greenchem_dataset.csv"
OUTPUT_DB = "greenchem_db.db"
TABLE_NAME = "chemicals"

# ── Lista semilla de químicos ────────────────────────────────────────────
FALLBACK_CHEMICALS = [
    "Water", "Sodium Chloride", "Sucrose", "Glycerin", "Citric Acid",
    "Formaldehyde", "Benzene", "Methanol", "Sulfuric Acid", "Ammonia",
    "Hydrogen Peroxide", "Acetone", "Toluene", "Xylene", "Chloroform",
    "Ethanol", "Sodium Hydroxide", "Hydrochloric Acid", "Lead(II) Nitrate",
    "Cadmium Oxide", "Arsenic Pentoxide", "Mercury(II) Chloride",
    "Potassium Cyanide", "Dioxane", "Acrylamide", "Phenol", "Styrene",
    "Naphthalene", "Diethyl phthalate"
]

AQUATIC_H_CODES = {"H400", "H401", "H402", "H410", "H411", "H412", "H413"}
TOXIC_H_CODES = {"H300", "H301", "H310", "H311", "H330", "H331", "H340",
                 "H350", "H360", "H361", "H370", "H372"}

# ═══════════════════════════════════════════════════════════════════════
# CLASES DEL PIPELINE ETL
# ═══════════════════════════════════════════════════════════════════════

class PubChemEnricher:
    """Cliente para la API REST de PubChem (PUG REST)."""

    DESIRED_PROPERTIES = "MolecularFormula,MolecularWeight,IsomericSMILES,IUPACName"

    def __init__(self, courtesy_delay: float = 1.5):
        self.courtesy_delay = courtesy_delay
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def _safe_request(self, url: str, timeout: int = 30) -> Optional[Dict]:
        try:
            time.sleep(self.courtesy_delay)
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 404:
                st.warning(f"⚠️ Compuesto no encontrado en PubChem.")
            else:
                st.error(f"❌ HTTP {response.status_code}: {e}")
            return None
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Error de red: {e}")
            return None
        except json.JSONDecodeError as e:
            st.error(f"❌ Error decodificando JSON: {e}")
            return None

    def search_by_name(self, name: str) -> Optional[int]:
        encoded_name = requests.utils.quote(name)
        url = f"{PUG_BASE}/compound/name/{encoded_name}/cids/JSON"
        data = self._safe_request(url)
        if data and "IdentifierList" in data:
            cids = data["IdentifierList"]["CID"]
            return cids[0] if cids else None
        return None

    def get_properties(self, cid: int) -> Dict[str, Any]:
        url = f"{PUG_BASE}/compound/cid/{cid}/property/{self.DESIRED_PROPERTIES}/JSON"
        data = self._safe_request(url)
        if data and "PropertyTable" in data:
            props = data["PropertyTable"]["Properties"][0]
            return {
                "cid": props.get("CID"),
                "molecular_formula": props.get("MolecularFormula", "N/A"),
                "molecular_weight": props.get("MolecularWeight", "N/A"),
                "smiles": props.get("IsomericSMILES", "N/A"),
                "iupac_name": props.get("IUPACName", "N/A"),
            }
        return {"cid": cid, "molecular_formula": "N/A", "molecular_weight": "N/A",
                "smiles": "N/A", "iupac_name": "N/A"}

    def get_ghs_classification(self, cid: int) -> Dict[str, Any]:
        url = f"{PUG_VIEW_BASE}/{cid}/JSON/?response_type=display&heading=GHS%20Classification"
        data = self._safe_request(url)
        if not data or "Record" not in data:
            return {
                "ghs_h_statements": [], "ghs_pictograms": [],
                "signal_word": "N/A", "aquatic_toxicity": False, "high_toxicity": False,
            }

        h_statements = []
        pictograms = []
        signal_word = "N/A"

        try:
            sections = data["Record"].get("Section", [])
            for section in sections:
                if section.get("TOCHeading") == "GHS Classification":
                    subsections = section.get("Section", [])
                    for sub in subsections:
                        info = sub.get("Information", [])
                        for item in info:
                            name = item.get("Name", "")
                            value = item.get("Value", {})

                            if name == "GHS Hazard Statements":
                                strings = value.get("StringWithMarkup", [])
                                for s in strings:
                                    text = s.get("String", "")
                                    match = re.search(r"H\d{3}[a-z]?", text)
                                    if match:
                                        h_statements.append({"code": match.group(), "description": text})

                            elif name == "Pictogram(s)":
                                strings = value.get("StringWithMarkup", [])
                                for s in strings:
                                    markup = s.get("Markup", [])
                                    for m in markup:
                                        if m.get("Type") == "Icon":
                                            pictograms.append(m.get("Extra", "Unknown"))

                            elif name == "Signal":
                                strings = value.get("StringWithMarkup", [])
                                if strings:
                                    signal_word = strings[0].get("String", "N/A")
        except Exception as e:
            st.warning(f"⚠️ Error parseando GHS para CID {cid}: {e}")

        h_codes = {h["code"] for h in h_statements}
        return {
            "ghs_h_statements": h_statements,
            "ghs_pictograms": list(set(pictograms)),
            "signal_word": signal_word,
            "aquatic_toxicity": bool(h_codes & AQUATIC_H_CODES),
            "high_toxicity": bool(h_codes & TOXIC_H_CODES),
        }

    def enrich_chemical(self, name: str) -> Optional[Dict[str, Any]]:
        st.info(f"🔬 Enriqueciendo: '{name}'")
        cid = self.search_by_name(name)
        if cid is None:
            st.warning(f"❌ No se encontró CID para '{name}'")
            return None

        st.success(f"✅ CID encontrado: {cid}")
        properties = self.get_properties(cid)
        ghs_data = self.get_ghs_classification(cid)

        return {
            "source_name": name,
            "pubchem_cid": properties["cid"],
            "iupac_name": properties["iupac_name"],
            "molecular_formula": properties["molecular_formula"],
            "molecular_weight": properties["molecular_weight"],
            "smiles": properties["smiles"],
            "signal_word": ghs_data["signal_word"],
            "ghs_h_codes": ", ".join([h["code"] for h in ghs_data["ghs_h_statements"]]) or "N/A",
            "ghs_h_descriptions": " | ".join([h["description"] for h in ghs_data["ghs_h_statements"]]) or "N/A",
            "ghs_pictograms": ", ".join(ghs_data["ghs_pictograms"]) or "N/A",
            "aquatic_toxicity": ghs_data["aquatic_toxicity"],
            "high_toxicity": ghs_data["high_toxicity"],
            "h_statements_count": len(ghs_data["ghs_h_statements"]),
            "enrichment_timestamp": datetime.now().isoformat(),
        }


class GreenChemPersistence:
    """Capa de persistencia dual: CSV + SQLite."""

    def __init__(self, csv_path: str = OUTPUT_CSV, db_path: str = OUTPUT_DB):
        self.csv_path = csv_path
        self.db_path = db_path
        self.df = None

    def build_dataframe(self, records: List[Dict[str, Any]]) -> pd.DataFrame:
        if not records:
            st.error("❌ No hay registros para persistir.")
            return pd.DataFrame()
        self.df = pd.DataFrame(records)
        self.df["molecular_weight"] = pd.to_numeric(self.df["molecular_weight"], errors="coerce")
        self.df["aquatic_toxicity"] = self.df["aquatic_toxicity"].astype(bool)
        self.df["high_toxicity"] = self.df["high_toxicity"].astype(bool)
        col_order = [
            "source_name", "pubchem_cid", "iupac_name", "molecular_formula",
            "molecular_weight", "smiles", "signal_word", "ghs_h_codes",
            "ghs_h_descriptions", "ghs_pictograms", "aquatic_toxicity",
            "high_toxicity", "h_statements_count", "enrichment_timestamp",
        ]
        self.df = self.df[[c for c in col_order if c in self.df.columns]]
        return self.df

    def export_to_csv(self) -> str:
        if self.df is None or self.df.empty:
            return ""
        try:
            self.df.to_csv(self.csv_path, index=False, encoding="utf-8")
            return self.csv_path
        except Exception as e:
            st.error(f"❌ Error exportando CSV: {e}")
            return ""

    def export_to_sqlite(self) -> str:
        if self.df is None or self.df.empty:
            return ""
        try:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_name TEXT NOT NULL, pubchem_cid INTEGER, iupac_name TEXT,
                molecular_formula TEXT, molecular_weight REAL, smiles TEXT,
                signal_word TEXT, ghs_h_codes TEXT, ghs_h_descriptions TEXT,
                ghs_pictograms TEXT, aquatic_toxicity INTEGER, high_toxicity INTEGER,
                h_statements_count INTEGER, enrichment_timestamp TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );"""
            cursor.execute(create_table_sql)
            cursor.execute(f"CREATE INDEX idx_cid ON {TABLE_NAME}(pubchem_cid);")
            cursor.execute(f"CREATE INDEX idx_aquatic ON {TABLE_NAME}(aquatic_toxicity);")
            cursor.execute(f"CREATE INDEX idx_toxicity ON {TABLE_NAME}(high_toxicity);")
            cursor.execute(f"CREATE INDEX idx_formula ON {TABLE_NAME}(molecular_formula);")

            insert_data = []
            for _, row in self.df.iterrows():
                insert_data.append((
                    row["source_name"], row["pubchem_cid"], row["iupac_name"],
                    row["molecular_formula"], row["molecular_weight"] if pd.notna(row["molecular_weight"]) else None,
                    row["smiles"], row["signal_word"], row["ghs_h_codes"],
                    row["ghs_h_descriptions"], row["ghs_pictograms"],
                    int(row["aquatic_toxicity"]), int(row["high_toxicity"]),
                    row["h_statements_count"], row["enrichment_timestamp"],
                ))

            insert_sql = f"""
            INSERT INTO {TABLE_NAME} (source_name, pubchem_cid, iupac_name, molecular_formula,
                molecular_weight, smiles, signal_word, ghs_h_codes, ghs_h_descriptions,
                ghs_pictograms, aquatic_toxicity, high_toxicity, h_statements_count, enrichment_timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""
            cursor.executemany(insert_sql, insert_data)
            conn.commit()
            conn.close()
            return self.db_path
        except Exception as e:
            st.error(f"❌ Error en persistencia: {e}")
            return ""


# ═══════════════════════════════════════════════════════════════════════
# FUNCIONES DE VISUALIZACIÓN
# ═══════════════════════════════════════════════════════════════════════

def get_toxicity_category(row):
    """Categoriza un compuesto según su toxicidad."""
    aquatic = bool(row.get('aquatic_toxicity', 0))
    high = bool(row.get('high_toxicity', 0))
    if aquatic and high:
        return '🔴 Ambas Toxicidades'
    elif high:
        return '🟠 Alta Toxicidad'
    elif aquatic:
        return '🟡 Toxicidad Acuática'
    else:
        return '🟢 Sin Toxicidad Detectada'


def plot_toxicity_heatmap(df):
    """Mapa de calor de toxicidad."""
    if df.empty:
        return None
    df_viz = df.copy()
    df_viz['aquatic_toxicity'] = df_viz['aquatic_toxicity'].astype(int)
    df_viz['high_toxicity'] = df_viz['high_toxicity'].astype(int)
    heatmap_data = df_viz[['source_name', 'aquatic_toxicity', 'high_toxicity']].set_index('source_name')

    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=['Toxicidad Acuática', 'Alta Toxicidad'],
        y=heatmap_data.index,
        colorscale=[[0, '#81C784'], [1, '#E53935']],
        showscale=True,
        colorbar=dict(tickvals=[0, 1], ticktext=['No Tóxico', 'Tóxico']),
    ))
    fig.update_layout(
        title='🗺️ Mapa de Calor de Toxicidad',
        xaxis_title='Tipo de Toxicidad',
        yaxis_title='Compuesto',
        height=max(400, len(df) * 25),
        margin=dict(l=150),
    )
    return fig


def plot_sustainability_radar(df, selected_chemicals=None):
    """Gráfico de radar de sostenibilidad."""
    if df.empty:
        return None

    df_viz = df.copy()
    df_viz['toxicity_score'] = df_viz['aquatic_toxicity'].astype(int) + df_viz['high_toxicity'].astype(int)
    df_viz['toxicity_radar'] = 10 - (df_viz['toxicity_score'] / 2) * 10

    np.random.seed(42)
    df_viz['biodegradability'] = np.random.randint(5, 11, size=len(df_viz))
    df_viz['carbon_footprint'] = np.random.randint(1, 6, size=len(df_viz))
    df_viz['cost'] = np.random.randint(1, 11, size=len(df_viz))
    df_viz['availability'] = np.random.randint(5, 11, size=len(df_viz))
    df_viz['carbon_footprint_radar'] = 10 - (df_viz['carbon_footprint'] / 5) * 10
    df_viz['cost_radar'] = 10 - (df_viz['cost'] / 10) * 10

    categories = ['Toxicidad', 'Biodegradabilidad', 'Huella Carbono', 'Costo', 'Disponibilidad']
    sample = df_viz.head(5) if selected_chemicals is None else df_viz[df_viz['source_name'].isin(selected_chemicals)]

    fig = go.Figure()
    colors = px.colors.qualitative.Set1

    for i, (_, row) in enumerate(sample.iterrows()):
        fig.add_trace(go.Scatterpolar(
            r=[row['toxicity_radar'], row['biodegradability'], row['carbon_footprint_radar'],
               row['cost_radar'], row['availability']],
            theta=categories,
            fill='toself',
            name=row['source_name'],
            line_color=colors[i % len(colors)],
        ))

    fig.update_layout(
        polar=dict(radialaxis=dict(range=[0, 10], showticklabels=True)),
        showlegend=True,
        title='🌿 Radar de Sostenibilidad',
        height=600,
    )
    return fig


def plot_toxicity_distribution(df):
    """Distribución de categorías de toxicidad (pie chart)."""
    if df.empty:
        return None
    df['toxicity_category'] = df.apply(get_toxicity_category, axis=1)
    counts = df['toxicity_category'].value_counts().reset_index()
    counts.columns = ['Categoría', 'Count']

    color_map = {
        '🔴 Ambas Toxicidades': '#C62828',
        '🟠 Alta Toxicidad': '#EF6C00',
        '🟡 Toxicidad Acuática': '#F9A825',
        '🟢 Sin Toxicidad Detectada': '#2E7D32',
    }

    fig = px.pie(counts, values='Count', names='Categoría',
                 title='📊 Distribución de Toxicidad',
                 color='Categoría', color_discrete_map=color_map,
                 hole=0.4, template='plotly_white')
    fig.update_traces(textposition='inside', textinfo='percent+label')
    return fig


def plot_molecular_weight_histogram(df):
    """Histograma de pesos moleculares."""
    if df.empty:
        return None
    df['molecular_weight'] = pd.to_numeric(df['molecular_weight'], errors='coerce')
    df_clean = df.dropna(subset=['molecular_weight'])
    if df_clean.empty:
        return None

    fig = px.histogram(df_clean, x='molecular_weight',
                       title='⚖️ Distribución de Pesos Moleculares',
                       labels={'molecular_weight': 'Peso Molecular (g/mol)', 'count': 'Compuestos'},
                       template='plotly_white', hover_name='source_name', marginal='rug',
                       color_discrete_sequence=['#2E7D32'])
    fig.update_layout(bargap=0.2, showlegend=False)
    return fig


def plot_molecular_weight_vs_toxicity(df):
    """Scatter plot: Peso Molecular vs Toxicidad."""
    if df.empty:
        return None
    df['molecular_weight'] = pd.to_numeric(df['molecular_weight'], errors='coerce')
    df['toxicity_category'] = df.apply(get_toxicity_category, axis=1)
    df_plot = df.dropna(subset=['molecular_weight', 'toxicity_category']).copy()
    if df_plot.empty:
        return None

    color_map = {
        '🔴 Ambas Toxicidades': '#C62828',
        '🟠 Alta Toxicidad': '#EF6C00',
        '🟡 Toxicidad Acuática': '#F9A825',
        '🟢 Sin Toxicidad Detectada': '#2E7D32',
    }

    fig = px.scatter(df_plot, x='molecular_weight', y='toxicity_category',
                     color='toxicity_category', color_discrete_map=color_map,
                     title='🔬 Peso Molecular vs. Categoría de Toxicidad',
                     labels={'molecular_weight': 'Peso Molecular (g/mol)', 'toxicity_category': 'Toxicidad'},
                     hover_name='source_name', template='plotly_white', size='h_statements_count',
                     size_max=30)
    return fig


def plot_h_statements_distribution(df):
    """Distribución de declaraciones GHS-H."""
    if df.empty:
        return None
    h_codes_filtered = df[df['ghs_h_codes'].notna() & (df['ghs_h_codes'] != 'N/A')].copy()
    if h_codes_filtered.empty:
        return None

    h_codes_filtered['ghs_h_codes_list'] = h_codes_filtered['ghs_h_codes'].apply(
        lambda x: [code.strip() for code in x.split(',')])
    h_statements_exploded = h_codes_filtered.explode('ghs_h_codes_list')
    h_statement_counts = h_statements_exploded['ghs_h_codes_list'].value_counts().reset_index()
    h_statement_counts.columns = ['H-Statement', 'Count']

    fig = px.bar(h_statement_counts, x='H-Statement', y='Count',
                 title='⚠️ Distribución de Declaraciones GHS-H',
                 labels={'H-Statement': 'Declaración GHS-H', 'Count': 'Ocurrencias'},
                 template='plotly_white', color='Count',
                 color_continuous_scale=px.colors.sequential.Plasma)
    fig.update_layout(xaxis_categoryorder='total descending', showlegend=False)
    return fig


def plot_pictograms_distribution(df):
    """Distribución de pictogramas GHS."""
    if df.empty:
        return None
    pictograms_filtered = df[df['ghs_pictograms'].notna() & (df['ghs_pictograms'] != 'N/A')].copy()
    if pictograms_filtered.empty:
        return None

    pictograms_filtered['ghs_pictograms_list'] = pictograms_filtered['ghs_pictograms'].apply(
        lambda x: [p.strip() for p in x.split(',')])
    pictograms_exploded = pictograms_filtered.explode('ghs_pictograms_list')
    pictogram_counts = pictograms_exploded['ghs_pictograms_list'].value_counts().reset_index()
    pictogram_counts.columns = ['Pictogram', 'Count']

    fig = px.bar(pictogram_counts, x='Pictogram', y='Count',
                 title='🎨 Distribución de Pictogramas GHS',
                 labels={'Pictogram': 'Pictograma GHS', 'Count': 'Ocurrencias'},
                 template='plotly_white', color='Count',
                 color_continuous_scale=px.colors.sequential.Viridis)
    fig.update_layout(xaxis_categoryorder='total descending', showlegend=False)
    return fig


def create_folium_map(df):
    """Mapa Folium con ubicaciones ficticias."""
    if df.empty:
        return None

    industrial_locations = [
        {'name': 'Rotterdam, Netherlands', 'lat': 51.9225, 'lon': 4.47917},
        {'name': 'Ruhr Area, Germany', 'lat': 51.4556, 'lon': 7.0115},
        {'name': 'Barcelona, Spain', 'lat': 41.3851, 'lon': 2.1734},
        {'name': 'Lyon, France', 'lat': 45.75, 'lon': 4.85},
        {'name': 'Antwerp, Belgium', 'lat': 51.2602, 'lon': 4.4062},
    ]

    sample = df.head(5).copy()
    np.random.seed(42)
    assigned_indices = np.random.choice(len(industrial_locations), len(sample), replace=True)
    sample['location_name'] = [industrial_locations[i]['name'] for i in assigned_indices]
    sample['latitude'] = [industrial_locations[i]['lat'] for i in assigned_indices]
    sample['longitude'] = [industrial_locations[i]['lon'] for i in assigned_indices]

    m = folium.Map(location=[sample['latitude'].mean(), sample['longitude'].mean()], zoom_start=6)
    for _, row in sample.iterrows():
        popup_html = f"<b>{row['source_name']}</b><br>CID: {row['pubchem_cid']}<br>Peso: {row['molecular_weight']}<br>Ubicación: {row['location_name']}"
        marker_color = 'red' if (row['aquatic_toxicity'] or row['high_toxicity']) else 'green'
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=row['source_name'],
            icon=folium.Icon(color=marker_color, icon='flask')
        ).add_to(m)
    return m


# ═══════════════════════════════════════════════════════════════════════
# FUNCIONES DE SIMULACIÓN
# ═══════════════════════════════════════════════════════════════════════

def simulate_substitution(original_name, substitute_name, toxicity_reduction_pct, cost_increase_pct, df):
    """Simula el impacto de sustituir un químico."""
    original = df[df['source_name'] == original_name]
    if original.empty:
        return None, "Químico original no encontrado"

    orig_tox = int(original['aquatic_toxicity'].iloc[0]) + int(original['high_toxicity'].iloc[0])
    orig_cost = 100  # Valor ficticio base

    new_tox = max(0, orig_tox * (1 - toxicity_reduction_pct))
    new_cost = orig_cost * (1 + cost_increase_pct)

    return {
        "original": original_name,
        "substitute": substitute_name,
        "orig_toxicity": orig_tox,
        "orig_cost": orig_cost,
        "new_toxicity": new_tox,
        "new_cost": new_cost,
        "tox_reduction": f"{toxicity_reduction_pct:.0%}",
        "cost_increase": f"{cost_increase_pct:.0%}",
    }, None


def simulate_regulatory_alerts(client_chemicals, regulatory_db, current_date):
    """Simula alertas regulatorias."""
    alerts = []
    for chem in client_chemicals:
        for reg in regulatory_db:
            if reg['chemical_name'].lower() == chem.lower():
                reg_date = datetime.strptime(reg['effective_date'], '%Y-%m-%d').date()
                if reg['status'] == 'restricted' and reg_date <= current_date:
                    alerts.append({
                        'chemical': chem,
                        'regulation': reg['regulation'],
                        'status': reg['status'],
                        'effective_date': reg['effective_date'],
                    })
    return alerts


# ═══════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/test-tube.png", width=80)
    st.markdown("### 🌿 GreenChem Score")
    st.markdown("---")

    page = st.radio("📂 Navegación", [
        "🏠 Inicio",
        "🔬 Pipeline ETL",
        "📊 Dashboard",
        "🗺️ Mapa Geográfico",
        "🧪 Simulador de Sustitución",
        "⚖️ Alertas Regulatorias",
        "📥 Descargas",
    ])

    st.markdown("---")
    st.markdown("**🛡️ Gobernanza Ética**")
    st.markdown("- User-Agent realista")
    st.markdown("- Delay de cortesía: 1.5s")
    st.markdown("- Manejo robusto de errores")
    st.markdown("- Trazabilidad completa")

    st.markdown("---")
    st.markdown("<div class='footer'>v1.0.0 | 2026</div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════
# PÁGINA: INICIO
# ═══════════════════════════════════════════════════════════════════════

if page == "🏠 Inicio":
    st.markdown("<div class='main-header'>🧪 GreenChem Score</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Pipeline ETL para Clasificación Química Sostenible</div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class='metric-card'>
            <h3>🔬 Extracción</h3>
            <p>Scraping ético de fuentes de datos abiertos con manejo robusto de errores y delay de cortesía.</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class='metric-card'>
            <h3>🧬 Enriquecimiento</h3>
            <p>Integración con PubChem PUG REST para obtener propiedades moleculares y clasificación GHS.</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class='metric-card'>
            <h3>💾 Persistencia</h3>
            <p>Exportación dual a CSV y SQLite con esquema indexado y trazabilidad completa.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📋 Flujo del Pipeline")
    st.markdown("""
    ```
    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
    │  Scraping   │───▶│  PubChem    │───▶│  CSV/SQLite │───▶│ Dashboard   │
    │  (Fuentes)  │    │  API (PUG)  │    │  Persistencia│    │ Streamlit   │
    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
    ```
    """)

    st.markdown("---")
    st.subheader("🎯 Base del Green Score")
    st.markdown("""
    | Código H | Descripción | Impacto |
    |----------|-------------|---------|
    | H400-H413 | Toxicidad acuática | 🔴 Crítico para ecosistemas |
    | H300-H372 | Toxicidad aguda/crónica | 🔴 Riesgo para salud humana |
    | Sin códigos | Compuestos seguros | 🟢 Puntuación alta de verde |
    """)


# ═══════════════════════════════════════════════════════════════════════
# PÁGINA: PIPELINE ETL
# ═══════════════════════════════════════════════════════════════════════

elif page == "🔬 Pipeline ETL":
    st.markdown("<div class='main-header'>🔬 Pipeline ETL</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Ejecuta el pipeline completo de extracción, enriquecimiento y persistencia</div>", unsafe_allow_html=True)

    st.info("💡 Este proceso consulta la API de PubChem. Puede tardar varios minutos dependiendo del número de compuestos.")

    # Selección de químicos
    st.subheader("1️⃣ Selección de Compuestos")
    use_fallback = st.checkbox("Usar lista semilla predefinida (recomendado para demo)", value=True)

    if use_fallback:
        selected_chemicals = st.multiselect(
            "Compuestos a analizar:",
            options=FALLBACK_CHEMICALS,
            default=FALLBACK_CHEMICALS[:15],
        )
    else:
        custom_input = st.text_area("Ingresa nombres de compuestos (uno por línea):", height=150)
        selected_chemicals = [c.strip() for c in custom_input.split("\n") if c.strip()]

    # Ejecución del pipeline
    if st.button("🚀 Ejecutar Pipeline ETL", type="primary"):
        if not selected_chemicals:
            st.error("❌ Selecciona al menos un compuesto.")
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()

            enricher = PubChemEnricher(courtesy_delay=COURTESY_DELAY)
            enriched_records = []

            for i, chemical in enumerate(selected_chemicals):
                status_text.text(f"🔬 Enriqueciendo {i+1}/{len(selected_chemicals)}: {chemical}")
                record = enricher.enrich_chemical(chemical)
                if record:
                    enriched_records.append(record)
                progress_bar.progress((i + 1) / len(selected_chemicals))

            status_text.text("✅ Enriquecimiento completado. Persistiendo datos...")

            # Persistencia
            persistence = GreenChemPersistence()
            df_clean = persistence.build_dataframe(enriched_records)
            csv_path = persistence.export_to_csv()
            db_path = persistence.export_to_sqlite()

            progress_bar.empty()
            status_text.empty()

            st.success(f"🎉 Pipeline completado: {len(enriched_records)}/{len(selected_chemicals)} compuestos exitosos.")

            col1, col2 = st.columns(2)
            with col1:
                st.metric("📄 CSV", csv_path if csv_path else "Fallido")
            with col2:
                st.metric("🗄️ SQLite", db_path if db_path else "Fallido")

            st.subheader("📊 Vista previa de datos enriquecidos")
            display_cols = ["source_name", "pubchem_cid", "molecular_formula", "molecular_weight", "signal_word", "aquatic_toxicity", "high_toxicity"]
            st.dataframe(df_clean[display_cols], use_container_width=True)

            # Guardar en session state
            st.session_state['df'] = df_clean
            st.session_state['pipeline_run'] = True


# ═══════════════════════════════════════════════════════════════════════
# PÁGINA: DASHBOARD
# ═══════════════════════════════════════════════════════════════════════

elif page == "📊 Dashboard":
    st.markdown("<div class='main-header'>📊 Dashboard</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Visualizaciones interactivas del dataset químico</div>", unsafe_allow_html=True)

    # Cargar datos
    df = None
    if 'df' in st.session_state and st.session_state['df'] is not None:
        df = st.session_state['df']
    elif os.path.exists(OUTPUT_CSV):
        try:
            df = pd.read_csv(OUTPUT_CSV)
        except Exception:
            pass

    if df is None or df.empty:
        st.warning("⚠️ No hay datos disponibles. Ejecuta el Pipeline ETL primero.")
        st.stop()

    # Métricas principales
    total = len(df)
    aquatic = int(df['aquatic_toxicity'].sum())
    high_tox = int(df['high_toxicity'].sum())
    safe = total - aquatic - high_tox

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class='metric-card'>
            <h2>{total}</h2>
            <p>Compuestos Analizados</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class='danger-card'>
            <h2>{aquatic}</h2>
            <p>Toxicidad Acuática ({aquatic/total*100:.1f}%)</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class='danger-card'>
            <h2>{high_tox}</h2>
            <p>Alta Toxicidad ({high_tox/total*100:.1f}%)</p>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class='metric-card'>
            <h2>{safe}</h2>
            <p>Potencialmente Seguros ({safe/total*100:.1f}%)</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Tabs de visualizaciones
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🗺️ Heatmap Toxicidad", "🌿 Radar Sostenibilidad", "📊 Distribución Toxicidad",
        "⚖️ Peso Molecular", "⚠️ H-Statements", "🎨 Pictogramas"
    ])

    with tab1:
        fig = plot_toxicity_heatmap(df)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos suficientes para el heatmap.")

    with tab2:
        selected = st.multiselect("Selecciona compuestos para el radar:", df['source_name'].tolist(), default=df['source_name'].head(3).tolist())
        fig = plot_sustainability_radar(df, selected)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos suficientes para el radar.")

    with tab3:
        fig = plot_toxicity_distribution(df)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos suficientes.")

    with tab4:
        col_a, col_b = st.columns(2)
        with col_a:
            fig = plot_molecular_weight_histogram(df)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        with col_b:
            fig = plot_molecular_weight_vs_toxicity(df)
            if fig:
                st.plotly_chart(fig, use_container_width=True)

    with tab5:
        fig = plot_h_statements_distribution(df)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay declaraciones GHS-H disponibles.")

    with tab6:
        fig = plot_pictograms_distribution(df)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay pictogramas GHS disponibles.")

    # Tabla de datos
    st.markdown("---")
    st.subheader("📋 Tabla de Compuestos")
    df['toxicity_category'] = df.apply(get_toxicity_category, axis=1)
    st.dataframe(df, use_container_width=True, height=400)


# ═══════════════════════════════════════════════════════════════════════
# PÁGINA: MAPA GEOGRÁFICO
# ═══════════════════════════════════════════════════════════════════════

elif page == "🗺️ Mapa Geográfico":
    st.markdown("<div class='main-header'>🗺️ Mapa Geográfico</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Ubicaciones industriales ficticias de compuestos químicos</div>", unsafe_allow_html=True)

    df = None
    if 'df' in st.session_state and st.session_state['df'] is not None:
        df = st.session_state['df']
    elif os.path.exists(OUTPUT_CSV):
        try:
            df = pd.read_csv(OUTPUT_CSV)
        except Exception:
            pass

    if df is None or df.empty:
        st.warning("⚠️ No hay datos disponibles. Ejecuta el Pipeline ETL primero.")
        st.stop()

    st.info("📍 Las ubicaciones mostradas son ficticias y representan centros industriales europeos seleccionados aleatoriamente para demostración.")

    m = create_folium_map(df)
    if m:
        st_folium(m, width=1200, height=600)
    else:
        st.info("No hay datos suficientes para generar el mapa.")


# ═══════════════════════════════════════════════════════════════════════
# PÁGINA: SIMULADOR DE SUSTITUCIÓN
# ═══════════════════════════════════════════════════════════════════════

elif page == "🧪 Simulador de Sustitución":
    st.markdown("<div class='main-header'>🧪 Simulador de Sustitución</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Evalúa el impacto de reemplazar un compuesto químico por una alternativa</div>", unsafe_allow_html=True)

    df = None
    if 'df' in st.session_state and st.session_state['df'] is not None:
        df = st.session_state['df']
    elif os.path.exists(OUTPUT_CSV):
        try:
            df = pd.read_csv(OUTPUT_CSV)
        except Exception:
            pass

    if df is None or df.empty:
        st.warning("⚠️ No hay datos disponibles. Ejecuta el Pipeline ETL primero.")
        st.stop()

    st.info("💡 Este simulador es conceptual. En una implementación real requeriría una base de datos de sustitutos y modelos de impacto.")

    col1, col2 = st.columns(2)
    with col1:
        original = st.selectbox("Químico Original:", df['source_name'].tolist())
    with col2:
        substitute = st.text_input("Químico Sustituto:", value="Bioplástico Genérico A")

    col3, col4 = st.columns(2)
    with col3:
        tox_reduction = st.slider("Reducción de Toxicidad (%):", 0, 100, 40) / 100
    with col4:
        cost_increase = st.slider("Aumento de Costo (%):", 0, 100, 15) / 100

    if st.button("🚀 Simular Sustitución", type="primary"):
        result, error = simulate_substitution(original, substitute, tox_reduction, cost_increase, df)
        if error:
            st.error(error)
        else:
            st.success("✅ Simulación completada")

            col_r1, col_r2, col_r3, col_r4 = st.columns(4)
            with col_r1:
                st.metric("Original", result['original'])
            with col_r2:
                st.metric("Sustituto", result['substitute'])
            with col_r3:
                st.metric("Reducción Toxicidad", result['tox_reduction'])
            with col_r4:
                st.metric("Aumento Costo", result['cost_increase'])

            # Gráfico comparativo
            comparison_data = pd.DataFrame({
                'Métrica': ['Toxicidad Original', 'Toxicidad Simulada', 'Costo Original', 'Costo Simulado'],
                'Valor': [result['orig_toxicity'], result['new_toxicity'], result['orig_cost'], result['new_cost']],
                'Tipo': ['Original', 'Simulado', 'Original', 'Simulado']
            })

            fig = px.bar(comparison_data, x='Métrica', y='Valor', color='Tipo',
                         color_discrete_map={'Original': '#42A5F5', 'Simulado': '#EF5350'},
                         title='📊 Comparación: Original vs. Simulado',
                         template='plotly_white', barmode='group')
            st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════
# PÁGINA: ALERTAS REGULATORIAS
# ═══════════════════════════════════════════════════════════════════════

elif page == "⚖️ Alertas Regulatorias":
    st.markdown("<div class='main-header'>⚖️ Alertas Regulatorias</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Monitoreo conceptual de regulaciones químicas</div>", unsafe_allow_html=True)

    st.info("💡 Este sistema es conceptual. En producción requeriría integración con APIs de agencias regulatorias (REACH, EPA, etc.).")

    # Base regulatoria ficticia
    regulatory_db = [
        {'chemical_name': 'Bisphenol A', 'regulation': 'Prohibición en biberones (UE)', 'status': 'restricted', 'effective_date': '2011-06-01'},
        {'chemical_name': 'Formaldehyde', 'regulation': 'Restricción en cosméticos', 'status': 'restricted', 'effective_date': '2025-01-01'},
        {'chemical_name': 'Acetone', 'regulation': 'Sin restricciones', 'status': 'safe', 'effective_date': '2000-01-01'},
        {'chemical_name': 'Benzene', 'regulation': 'Prohibición general industrial', 'status': 'restricted', 'effective_date': '2010-01-01'},
        {'chemical_name': 'Lead(II) Nitrate', 'regulation': 'REACH SVHC', 'status': 'restricted', 'effective_date': '2012-06-18'},
    ]

    df = None
    if 'df' in st.session_state and st.session_state['df'] is not None:
        df = st.session_state['df']
    elif os.path.exists(OUTPUT_CSV):
        try:
            df = pd.read_csv(OUTPUT_CSV)
        except Exception:
            pass

    if df is not None and not df.empty:
        client_chems = df['source_name'].tolist()
    else:
        client_chems = FALLBACK_CHEMICALS[:10]

    st.subheader("🔍 Químicos del Cliente")
    st.write(f"Monitoreando {len(client_chems)} compuestos:")
    st.write(", ".join(client_chems))

    # Simular alertas actuales
    current_alerts = simulate_regulatory_alerts(client_chems, regulatory_db, datetime.now().date())

    st.subheader("🚨 Alertas Activas")
    if current_alerts:
        for alert in current_alerts:
            st.markdown(f"""
            <div class='danger-card'>
                <h4>⚠️ {alert['chemical']}</h4>
                <p><b>Regulación:</b> {alert['regulation']}</p>
                <p><b>Efectiva desde:</b> {alert['effective_date']}</p>
                <p><b>Estado:</b> {alert['status'].upper()}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class='metric-card'>
            <h4>✅ Sin Alertas Activas</h4>
            <p>No se detectaron restricciones regulatorias para los compuestos monitoreados hasta la fecha actual.</p>
        </div>
        """, unsafe_allow_html=True)

    # Simular alertas futuras
    st.subheader("🔮 Alertas Futuras (Simulación 2025-03-15)")
    future_date = datetime(2025, 3, 15).date()
    future_alerts = simulate_regulatory_alerts(client_chems, regulatory_db, future_date)

    if future_alerts:
        for alert in future_alerts:
            st.markdown(f"""
            <div class='warning-card'>
                <h4>⏰ {alert['chemical']}</h4>
                <p><b>Regulación:</b> {alert['regulation']}</p>
                <p><b>Efectiva desde:</b> {alert['effective_date']}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No se detectaron alertas futuras adicionales.")


# ═══════════════════════════════════════════════════════════════════════
# PÁGINA: DESCARGAS
# ═══════════════════════════════════════════════════════════════════════

elif page == "📥 Descargas":
    st.markdown("<div class='main-header'>📥 Descargas</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Exporta los datos enriquecidos en diferentes formatos</div>", unsafe_allow_html=True)

    df = None
    if 'df' in st.session_state and st.session_state['df'] is not None:
        df = st.session_state['df']
    elif os.path.exists(OUTPUT_CSV):
        try:
            df = pd.read_csv(OUTPUT_CSV)
        except Exception:
            pass

    if df is None or df.empty:
        st.warning("⚠️ No hay datos disponibles. Ejecuta el Pipeline ETL primero.")
        st.stop()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("📄 CSV")
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        st.download_button(
            label="⬇️ Descargar CSV",
            data=csv_buffer.getvalue(),
            file_name="greenchem_dataset.csv",
            mime="text/csv",
        )

    with col2:
        st.subheader("📊 Excel")
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Chemicals')
        st.download_button(
            label="⬇️ Descargar Excel",
            data=excel_buffer.getvalue(),
            file_name="greenchem_dataset.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    with col3:
        st.subheader("🗄️ SQLite")
        if os.path.exists(OUTPUT_DB):
            with open(OUTPUT_DB, "rb") as f:
                db_bytes = f.read()
            st.download_button(
                label="⬇️ Descargar SQLite",
                data=db_bytes,
                file_name="greenchem_db.db",
                mime="application/x-sqlite3",
            )
        else:
            st.info("Base de datos no generada aún.")

    st.markdown("---")
    st.subheader("📋 Resumen del Dataset")
    st.dataframe(df.describe(), use_container_width=True)


# ── Footer global ──────────────────────────────────────────────────────
st.markdown("""
<div class='footer'>
    🌿 GreenChem Score | Pipeline ETL para Química Sostenible | 2026<br>
    Datos proporcionados por <a href='https://pubchem.ncbi.nlm.nih.gov/' target='_blank'>PubChem NCBI</a>
</div>
""", unsafe_allow_html=True)
