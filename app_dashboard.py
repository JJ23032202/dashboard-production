import datetime as dt
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import os
import matplotlib.pyplot as plt
import signal
import sys

# ================= CONFIGURACIÓN DE PÁGINA =================
st.set_page_config(page_title="TIER Dashboard", layout="wide")


# ================= CSS GLOBAL (COMPACTO Y LETRA GRANDE) =================
st.markdown("""
<style>
.block-container {
    padding-top: 0.3rem;
    padding-bottom: 0.3rem;
    padding-left: 0.6rem;
    padding-right: 0.6rem;
}
h1, h2, h3 {
    margin-bottom: 0.1rem;
}
[data-testid="stDataFrame"] {
    font-size: 25px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* Reduce espacio superior general */
.block-container {
    padding-top: 0.4rem;
}

/* Reduce espacio en sidebar */
section[data-testid="stSidebar"] > div {
    padding-top: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

KPI_COLORS = {
    "verde": {
        "TESLA": "#2FFF05",        # verde claro
        "STELLANTIS": "#1FAF03"    # verde más oscuro
    },
    "naranja": {
        "TESLA": "#FFB347",
        "STELLANTIS": "#FF8C1A"
    },
    "azul": {
        "TESLA": "#5BC8FF",
        "STELLANTIS": "#0096D6"
    },
    "amarillo": {
        "TESLA": "#FFE066",
        "STELLANTIS": "#FFC107"
    }
}

# ================= FUNCIONES AUXILIARES =================
def get_val(row, col, suf=""):
    try:
        v = row[col]
        return "-" if pd.isna(v) else f"{v}{suf}"
    except Exception:
        return "-"

def abc_line(A, B, C, col, suf=""):
    def v(r):
        return "-" if r is None or pd.isna(r[col]) else f"{r[col]}{suf}"
    return f"TA: {v(A)} | TB: {v(B)} | TC: {v(C)}"


def card(title, body, bg):
    st.markdown(
        f"""
        <div style="
            background:{bg};
            border-radius:6px;
            padding:8px 12px;
            margin-bottom:6px;
            color:#000000;
        ">
            <div style="
                font-size:25px;
                font-weight:800;
                color:#000000;
                margin-bottom:4px;
            ">
                {title}
            </div>
            <div style="
                font-size:20px;
                font-weight:700;
                color:#000000;
                line-height:1.3;
            ">
                {body}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
def to_percent(v):

    """ Convierte a porcentaje de forma robusta para datos de LE:
    - 0.86  → 86
    - 1.10  → 110
    - 68    → 68
    """
    try:
        v = float(v)
        return v * 100 if v < 2 else v
    except Exception:
        return None

# ================= SIDEBAR =================
st.sidebar.header("📂 Carga de datos")
uploaded_file = st.sidebar.file_uploader(
    "Sube el Excel del TIER (TESLA + STELLANTIS)",
    type=["xlsx"]
)
if uploaded_file is None:
    st.sidebar.warning("⬆️ Sube el archivo para continuar")
    st.stop()
xls = pd.ExcelFile(uploaded_file)
# ================= LECTURA DE DATOS =================
DATA = {
    "TESLA": {
        "tier": pd.read_excel(xls, "TIER_MAIN_TESLA"),
        "le_codigo": pd.read_excel(xls, "LE_CODIGO_TESLA"),
    },
    "STELLANTIS": {
        "tier": pd.read_excel(xls, "TIER_MAIN_STELLANTIS"),
        "le_codigo": pd.read_excel(xls, "LE_CODIGO_STELLANTIS"),
    }
}

#fecha y semana
fecha = st.date_input(
    "Fecha",
    value=dt.date.today()
)
def obtener_semana_id(fecha):
    anio, semana, _ = fecha.isocalendar()
    return f"{anio}-W{semana:02d}"
semana_id = obtener_semana_id(fecha)

# ================= FUNCIÓN PRINCIPAL DEL DASHBOARD =================

def render_dashboard(plataforma, data, fecha, semana_id):
    df = data["tier"].copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["shift"] = df["shift"].astype(str).str.upper().str.strip()

    df_dia = df[df.date.dt.date == fecha]
    if df_dia.empty:
        st.warning(f"Sin datos para {plataforma}")
        return
    verde = KPI_COLORS["verde"][plataforma]

    A = df_dia[df_dia["shift"] == "A"].iloc[0] if not df_dia[df_dia["shift"] == "A"].empty else None
    B = df_dia[df_dia["shift"] == "B"].iloc[0] if not df_dia[df_dia["shift"] == "B"].empty else None
    C = df_dia[df_dia["shift"] == "C"].iloc[0] if not df_dia[df_dia["shift"] == "C"].empty else None

    # ===== HEADER =====
    st.markdown(f"## {plataforma} – TIER GENERAL  \n{fecha}")

    # ===== KPIs VERDES =====
    k1,k2,k3 = st.columns(3)
    with k1:
        card("% LE Turno🔂🆗", abc_line(A,B,C,"le_turno","%"), verde)
    with k2:
        card("Eficiencia Día📈☀️",f"Actual: {get_val(A,'le_dia_actual','%')}\nForecast: {get_val(A,'le_dia_forecast','%')}",verde)
    with k3:
        card("Eficiencia Mes📉📆", f"Actual: {get_val(A,'ef_mes_actual','%')}\nForecast: {get_val(A,'ef_mes_forecast','%')}",verde)

col_tesla, col_stellantis = st.columns(2)
with col_tesla:
    render_dashboard(
        plataforma="TESLA",
        data=DATA["TESLA"],
        fecha=fecha,
        semana_id=semana_id
    )

with col_stellantis:
    render_dashboard(
        plataforma="STELLANTIS",
        data=DATA["STELLANTIS"],
        fecha=fecha,
        semana_id=semana_id
    )


# ================= GRÁFICA LE TOTAL PLANTA =================
df = pd.read_excel(xls, "LE_HISTORICO")

# Normalizar columnas
df.columns = df.columns.astype(str).str.strip()

# Filtrar semana seleccionada
df_week = df[df["semana_id"] == semana_id]
if df_week.empty:
    st.warning("Sin datos históricos")
else:
    # Separar filas
    row_actual = df_week[df_week.iloc[:, 1] == "Actual"].iloc[0]
    row_msd = df_week[df_week.iloc[:, 1] == "MSD"].iloc[0]

    # Extraer valores (ya vienen en %)

    val_tesla = to_percent(row_actual["TESLA.4"])
    val_stell = to_percent(row_actual["STELLANTIS.4"])
    val_planta = to_percent(row_actual["Total _Planta"])
    val_msd = to_percent(row_msd["Total _Planta"])


    x = [0, 1, 2]

    fig, ax = plt.subplots(figsize=(9.5, 2.0))
    fig.patch.set_facecolor("#000000")
    ax.set_facecolor("#000000")
    bar_width = 0.28

    # Barras
    ax.bar(x[0], val_tesla, width=bar_width, color="#B8C0BC", label="TESLA")
    ax.bar(x[1], val_stell, width=bar_width, color="#00B7FF", label="STELLANTIS")
    ax.bar(x[2], val_planta, width=bar_width, color="#DD32FF", label="TOTAL PLANTA")

    # Línea MSD
    ax.plot(x, [val_msd]*3, "--o", color="#44CA32", linewidth=2, label="MSD")

    # Etiquetas
    for i, v in enumerate([val_tesla, val_stell, val_planta]):
        ax.text(
            i,
            v - 30,
            f"{v:.1f}%",
            ha="center",
            va="top",
            fontsize=9,
            color="black" if i == 2 else "white",
            rotation=90
        )

    for xi in x:
        ax.text(
            xi,
            val_msd + 6,
            f"{val_msd:.1f}%",
            ha="center",
            va="bottom",
            fontsize=9,
            color="#44CA32"
        )

    # Ejes
    ax.set_ylim(0, 180)
    ax.set_xticks(x)
    #ax.set_xticklabels(["TESLA", "STELLANTIS", "TOTAL"], color="white")
    ax.tick_params(axis="y", colors="white")

    ax.spines["left"].set_color("white")
    ax.spines["bottom"].set_color("white")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    leg = ax.legend(
        loc="lower center",
        bbox_to_anchor=(0.5, -0.4),
        ncol=4,
        frameon=False,
        fontsize=8
    )
    for t in leg.get_texts():
        t.set_color("white")
    ax.margins(x=0.25)
    plt.tight_layout(pad=1.0)
    st.pyplot(fig, use_container_width=True)


# ================= QUEJAS =================
def render_quejas(data, fecha, titulo):
    df = data["tier"].copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df_dia = df[df.date.dt.date == fecha]
    bg = KPI_COLORS["amarillo"][titulo]  
    if df_dia.empty:
        st.warning(f"Sin datos de quejas para {titulo}")
        return

    # Target y total del día (último registro válido)
    target = df_dia["quejas_target"].dropna().iloc[-1] \
        if "quejas_target" in df_dia.columns and not df_dia["quejas_target"].dropna().empty else "-"

    total = df_dia["quejas_actuales"].dropna().iloc[-1] \
        if "quejas_actuales" in df_dia.columns and not df_dia["quejas_actuales"].dropna().empty else 0

    # Detalle de quejas
    qdf = df_dia[
        df_dia["quejas_cuales"].notna() &
        (df_dia["quejas_cuales"].astype(str).str.strip() != "")
    ][["quejas_cuales", "quejas_codigo"]]

    if qdf.empty:
        texto = "_Sin quejas registradas_"
    else:
        texto = "\n".join(
            f"• {r.quejas_cuales} ({r.quejas_codigo})"
            for _, r in qdf.iterrows()
        )

    # Render
    st.markdown(
        f"""
        <div style="
            background:{bg};
            color:#000000;
            padding:10px;
            border-radius:6px;
            font-size:18px;
        ">
            <b>{titulo} – Quejas</b><br>
            Objetivo: <b>{target}</b> | Total: <b>{total}</b>
            <div style="
                max-height:160px;
                overflow-y:auto;
                margin-top:6px;
                font-size:17px;
            ">
            {texto.replace(chr(10), '<br>')}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
# ================= QUEJAS COMPARATIVAS =================
q1, q2 = st.columns(2)

with q1:
    render_quejas(DATA["TESLA"], fecha, "TESLA")

with q2:
    render_quejas(DATA["STELLANTIS"], fecha, "STELLANTIS")


# ================= KPIs NARANJAS =================
def render_kpis_naranjas(plataforma, data, fecha):
    df = data["tier"].copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["shift"] = df["shift"].astype(str).str.upper().str.strip()

    df_dia = df[df.date.dt.date == fecha]
    if df_dia.empty:
        st.warning("Sin datos de producción")
        return
    naranja = KPI_COLORS["naranja"][plataforma]
    A = df_dia[df_dia["shift"] == "A"].iloc[0] if not df_dia[df_dia["shift"] == "A"].empty else None
    B = df_dia[df_dia["shift"] == "B"].iloc[0] if not df_dia[df_dia["shift"] == "B"].empty else None
    C = df_dia[df_dia["shift"] == "C"].iloc[0] if not df_dia[df_dia["shift"] == "C"].empty else None

    # ---------- Producción / OEE / Scrap ----------
    p1, p2, p3 = st.columns([2.2, 1.3, 1.6])

    with p1:card("Producción 🛠️",f"""Pzas Construidas:{abc_line(A,B,C,'pzs_const')}<br>Defectos Acum:{abc_line(A,B,C,'defectos_acum')}<br><span style="font-size:25px"> DPMUs:{abc_line(A,B,C,'dpmus')}</span>""", naranja)

    with p2:card("OEE ✂️",f"""Objetivo: {get_val(A,'oee_target')}<br>Actual:   {get_val(A,'oee_actual')}<br>Acum:     {get_val(A,'oee_acum')}""",naranja)

    with p3:card("SCRAP 🚮",f"""Actual:{abc_line(A,B,C,'scrap_actual')}<br>Acumulado:{abc_line(A,B,C,'scrap_acum')}""",naranja)

# ================= KPIs NARANJAS – PRODUCCIÓN / OEE / SCRAP =================
st.markdown("")
p_tesla, p_stellantis = st.columns(2)

with p_tesla:
    render_kpis_naranjas("TESLA",DATA["TESLA"], fecha)

with p_stellantis:
    render_kpis_naranjas("STELLANTIS",DATA["STELLANTIS"], fecha)


# ================= KPIs AZULES =================
def render_kpis_azules(plataforma, data, fecha):
    df = data["tier"].copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["shift"] = df["shift"].astype(str).str.upper().str.strip()
    azul = KPI_COLORS["azul"][plataforma]
    df_dia = df[df.date.dt.date == fecha]
    if df_dia.empty:
        st.warning("Sin datos de census / ausentismo")
        return

    A = df_dia[df_dia["shift"] == "A"].iloc[0] if not df_dia[df_dia["shift"] == "A"].empty else None
    B = df_dia[df_dia["shift"] == "B"].iloc[0] if not df_dia[df_dia["shift"] == "B"].empty else None
    C = df_dia[df_dia["shift"] == "C"].iloc[0] if not df_dia[df_dia["shift"] == "C"].empty else None

    c1, c2, c3 = st.columns([1, 2.4, 1.2])

    # ---------- Census ----------
    with c1:card("<b>Census 🚻<br>",f"""<b>Total: {get_val(A,'census_total')}<br>TA: {get_val(A,'census_turno')}<br>TB: {get_val(B,'census_turno')}<br>TC: {get_val(C,'census_turno')}<br><br>""", azul)
    # ---------- Ausentismo ----------
    with c2: card("<b>Ausentismo 🧍<br>",f"""<b>Injustificado: {abc_line(A,B,C,'aus_injust')}<br><b>Controlado: {abc_line(A,B,C,'aus_control')}<br><b>Rotación: {abc_line(A,B,C,'rotacion')}<br><b>TLO: {abc_line(A,B,C,'tlo')}<b><br>C‑39: {abc_line(A,B,C,'c39')}""",azul)
    # ---------- Seguridad ----------
    with c3: card("<b>Seguridad 🚨<br>",f"""<b>Transporte:<br>{abc_line(A,B,C,'ehs_transporte')}<br> <b>Incidentes:<br>{abc_line(A,B,C,'ehs_incidentes')}<br><br>""",azul)

#==== KPIs AZULES – CENSUS / AUSENTISMO / SEGURIDAD =================
st.markdown("")

a_tesla, a_stellantis = st.columns(2)

with a_tesla:
    render_kpis_azules("TESLA",DATA["TESLA"], fecha)

with a_stellantis:
    render_kpis_azules("STELLANTIS",DATA["STELLANTIS"], fecha)

# ================= LEER DATOS SEMANALES =================
def leer_detractores_por_semana(xls, semana_id, sheet_name):
    df = pd.read_excel(xls, sheet_name)
    df.columns = df.columns.astype(str).str.strip()
    st.markdown("####Detractores")
    cols = [
        "semana_id",
        "concepto",
        "Lunes", "%LE TLunes",
        "Martes", "%LE TMartes",
        "Miercoles", "%LE Tmiercoles",
        "Jueves", "%LE TJueves",
        "Viernes", "%LE TViernes",
        "Total Semana", "%LE Total"
    ]

    df_t = df[cols].copy()

    df_t["semana_id"] = df_t["semana_id"].ffill().astype(str).str.strip()
    df_t = df_t[df_t["semana_id"] == semana_id]
    df_t = df_t[df_t["concepto"].notna()]

    # Convertir %LE a porcentaje real
    for col in df_t.columns:
        if col.lower().startswith("%le"):
            df_t[col] = pd.to_numeric(df_t[col], errors="coerce")
            df_t[col] = df_t[col].apply(
                lambda x: x * 100 if pd.notna(x) and x < 2 else x
            )

    return df_t.set_index("concepto")

df_det_planta = leer_detractores_por_semana(
    xls,
    semana_id,
    sheet_name="DETRACTORES"
)

if df_det_planta.empty:
    st.warning("Sin datos de detractores")
else:
    def format_det(x, es_pct=False):
        if isinstance(x, (int, float)) and pd.notna(x):
            return f"{x:.1f}%" if es_pct else f"{x:.1f}"
        return x

    formatos = {}
    for c in df_det_planta.columns:
        formatos[c] = lambda x, p=c.lower().startswith("%le"): format_det(x, p)

    st.dataframe(
        df_det_planta.style.format(formatos, na_rep="-"),
        use_container_width=True
    )

def leer_le_codigo_por_semana(xls, semana_id, turno, sheet_name):
    df = pd.read_excel(xls, sheet_name)
    df.columns = df.columns.astype(str).str.strip()


    col_codigo = next((c for c in df.columns if "codigo" in c.lower()), None)
    if col_codigo is None:
        return pd.DataFrame()

    if turno == "A":
        base = ["semana_id", "shift", col_codigo]
        suf = ""
    else:
        base = ["semana_id.1", "shift.1", f"{col_codigo}.1"]
        suf = ".1"

   
    cols = base + [
        f"Lunes{suf}", f"Martes{suf}",
        f"Miercoles{suf}", f"Jueves{suf}",
        f"Viernes{suf}", f"Total Semana{suf}"
    ]
    cols = [c for c in cols if c in df.columns]
    df_t = df[cols].copy()

    new_cols = {cols[0]: "semana_id", cols[1]: "shift", cols[2]: "codigo"}
    for c in cols[3:]:
        new_cols[c] = c.replace(suf, "")

    df_t = df_t.rename(columns=new_cols)

    df_t["semana_id"] = df_t["semana_id"].ffill().astype(str).str.strip()
    df_t = df_t[df_t["semana_id"] == semana_id]
    df_t = df_t[df_t["codigo"].astype(str).str.strip() != ""]

    for c in df_t.columns:
        if c not in ("semana_id", "shift", "codigo"):
            df_t[c] = pd.to_numeric(df_t[c], errors="coerce")
            df_t[c] = df_t[c].apply(lambda x: x * 100 if pd.notna(x) and x < 2 else x)

    return df_t.set_index("codigo")

turno_tabla = st.radio(
    "Turno",
    ["A", "B"],
    horizontal=True
)

c1, c2 = st.columns(2)

# -------- TESLA --------
with c1:
    st.markdown("#### % LE por Código – TESLA")
    
    df_cod_tesla = leer_le_codigo_por_semana(
        xls, semana_id, turno_tabla, "LE_CODIGO_TESLA"
    )

    if df_cod_tesla.empty:
        st.warning("Sin datos")
    else:

        num_cols = df_cod_tesla.select_dtypes(include="number").columns

        st.dataframe(
            df_cod_tesla.style.format(
                {c: "{:.1f}%" for c in num_cols},
                na_rep="-"
            ),
            use_container_width=True
        )



# -------- STELLANTIS --------
with c2:
    st.markdown("#### % LE por Código – STELLANTIS")

    df_cod_stell = leer_le_codigo_por_semana(
        xls, semana_id, turno_tabla, "LE_CODIGO_STELLANTIS"
    )

    if df_cod_stell.empty:
        st.warning("Sin datos")
    else:
        num_cols = df_cod_stell.select_dtypes(include="number").columns

        st.dataframe(
            df_cod_stell.style.format(
                {c: "{:.1f}%" for c in num_cols},
                na_rep="-"
            ),
            use_container_width=True
        )


