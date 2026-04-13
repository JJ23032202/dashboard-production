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
# ================= SIDEBAR =================
st.sidebar.header("📂 Carga de datos")

plataforma = st.sidebar.selectbox(
    "Plataforma a visualizar",
    ["TESLA", "STELLANTIS"]
)

uploaded_file = st.sidebar.file_uploader(
    f"Sube el Excel de {plataforma}",
    type=["xlsx"],
    key=f"uploader_{plataforma}"
)
if "excel_files" not in st.session_state:
    st.session_state["excel_files"] = {}

if uploaded_file is not None:
    st.session_state["excel_files"][plataforma] = uploaded_file
    st.sidebar.success(f"Archivo de {plataforma} cargado ✅")


if plataforma not in st.session_state["excel_files"]:

    # Espaciador superior para bajar el mensaje
    st.markdown("<div style='height:140px'></div>", unsafe_allow_html=True)

    with st.container():
        st.warning(f"⬆️ Sube primero el archivo de {plataforma} para continuar")

    st.stop()



uploaded_file = st.session_state["excel_files"][plataforma]

xls = pd.ExcelFile(uploaded_file)

# ================= LECTURA DE DATOS =================
df = pd.read_excel(xls, "TIER_MAIN")
df_cod = pd.read_excel(xls, "LE_CODIGO")
df_det = pd.read_excel(xls, "DETRACTORES")

df['date'] = pd.to_datetime(df['date'], errors='coerce')
df["shift"] = df["shift"].astype(str).str.upper().str.strip()


today = dt.date.today()

min_date = df['date'].dropna().min().date()
max_date = df['date'].dropna().max().date()

default_date = today if min_date <= today <= max_date else max_date

fecha = st.date_input(
    "Fecha",
    min_value=min_date,
    max_value=max_date,
    value=default_date
)


df_dia = df[df.date.dt.date == fecha]
if df_dia.empty:
    st.stop()

A = df_dia[df_dia["shift"] == "A"].iloc[0] if not df_dia[df_dia["shift"]=="A"].empty else None
B = df_dia[df_dia["shift"] == "B"].iloc[0] if not df_dia[df_dia["shift"]=="B"].empty else None
C = df_dia[df_dia["shift"] == "C"].iloc[0] if not df_dia[df_dia["shift"]=="C"].empty else None

row = df_dia.iloc[-1]


def obtener_semana_id(fecha):
    anio, semana, _ = fecha.isocalendar()
    return f"{anio}-W{semana:02d}"

semana_id = obtener_semana_id(fecha)

h1, h2 = st.columns([6, 1])

with h1:
    st.markdown(f"## {plataforma} – TIER GENERAL | {fecha}")

with h2:
    st.image("aptiv_logo.png", width=200)

# DEBUG (opcional - puedes quitar después)
st.write("Semana calculada:", semana_id)


def ultimo_valor(df, col, fecha):
    if col not in df.columns:
        return None
    s = df[df.date.dt.date <= fecha][col].dropna()
    return s.iloc[-1] if not s.empty else None

# Valores LE
le_dia_actual = ultimo_valor(df, "le_dia_actual", fecha)
le_dia_forecast = ultimo_valor(df, "le_dia_forecast", fecha)

ef_mes_actual = ultimo_valor(df, "ef_mes_actual", fecha)
ef_mes_forecast = ultimo_valor(df, "ef_mes_forecast", fecha)

# OEE
oee_actual = ultimo_valor(df, "oee_actual", fecha)
oee_acum = ultimo_valor(df, "oee_acum", fecha)
oee_target = ultimo_valor(df, "oee_target", fecha)

# Quejas target
quejas_target_dia = ultimo_valor(df, "quejas_target", fecha)
quejas_actual_dia = ultimo_valor(df, "quejas_actuales", fecha)
# ================= KPIs (10) =================
k1,k2,k3,k4,k5= st.columns(5)

with k1: card("Primera Hora🕕", abc_line(A,B,C,"des_primera_hora","%"), "#2FFF05")
with k2: card("Última Hora🕒", abc_line(A,B,C,"des_ultima_hora","%"), "#2FFF05")
with k3: card("% LE Turno🔂🆗", abc_line(A,B,C,"le_turno","%"), "#2FFF05")
with k4: card("Eficiencia del Día📈☀️",f"""Actual: {le_dia_actual if le_dia_actual is not None else "-"}% |  Forecast: {le_dia_forecast if le_dia_forecast is not None else "-"}%""", "#2FFF05")
with k5: card("Eficiencia del Mes📉📆",f"""Actual: {ef_mes_actual if ef_mes_actual is not None else "-"}% | Forecast: {ef_mes_forecast if ef_mes_forecast is not None else "-"}%""", "#2FFF05")


if (
    A is not None
    and "census_total" in A
    and pd.notna(A["census_total"])
):
    census_total = A["census_total"]
else:
    census_total = "-"


# ================= QUEJAS + GRÁFICA =================

def quejas_target_diario(df_dia):
    if "quejas_target" not in df_dia.columns:
        return None
    s = df_dia["quejas_target"].dropna()
    return s.iloc[-1] if not s.empty else None

q, g = st.columns([2,3])

if "quejas_codigo" in df_dia.columns:
    qdf = df_dia[
        df_dia["quejas_codigo"].notna() &
        (df_dia["quejas_codigo"].astype(str).str.strip() != "")
    ][["quejas_cuales", "quejas_codigo"]]

    total_quejas = len(qdf)

    qtxt = (
        "_Sin quejas_"
        if qdf.empty
        else "<br>".join(
            f"• {r.quejas_cuales} ({r.quejas_codigo})"
            for _, r in qdf.iterrows()
        )
    )
else:
    total_quejas = 0
    qtxt = "_Sin quejas_"

quejas_target_dia = quejas_target_diario(df_dia)

with q:
    st.markdown(
f"""<div style="
background:#E6FF04;
border-radius:6px;
padding:12px 14px;
color:#000000;
min-height:440px;
display:flex;
flex-direction:column;
">

<div style="font-size:25px; font-weight:800; margin-bottom:8px;">
Quejas📝⚠️
</div>

<div style="font-size:23px; font-weight:700; line-height:1.4; margin-bottom:8px;">
<b>Objetivo:</b> {quejas_target_dia if quejas_target_dia is not None else "-"}<br>
<b>Total:</b> {total_quejas}
</div>

<div style="font-size:23px; font-weight:600; line-height:1.45;">
{qtxt}
</div>

</div>""",
        unsafe_allow_html=True
    )

# --- Gráfica ---


SHEET_HIST = "LE_HISTORICO"

df_raw = pd.read_excel(xls, SHEET_HIST)

# Primera columna = KPI
df_raw = df_raw.rename(columns={df_raw.columns[0]: "KPI"})
df_raw = df_raw.set_index("KPI")

# Transponer para graficar
df_hist = (
    df_raw
    .T
    .reset_index()
    .rename(columns={
        "index": "periodo",
        "Actual": "actual",
        "BBP": "bbp",
        "MSD": "msd"
    })
)

for c in ["actual", "bbp", "msd"]:
    df_hist[c] = (
        pd.to_numeric(df_hist[c], errors="coerce") * 100
    )

x = range(len(df_hist))

fig, ax = plt.subplots(figsize=(6.8, 2.6))
fig.patch.set_facecolor("#000000")
ax.set_facecolor("#000000")

# Barras Actual
ax.bar(
    x,
    df_hist["actual"],
    width=0.6,
    color="#00CC63",
    label="Actual"
)

# Líneas BBP / MSD
ax.plot(x, df_hist["bbp"], "-o", color="#FE8002", label="BBP", markersize=4)
ax.plot(x, df_hist["msd"], "--o", color="#A7A7A7", label="MSD", markersize=4)

# -------- ETIQUETAS DE VALORES --------

# Valores de las barras (Actual)
for i, v in enumerate(df_hist["actual"]):
    if pd.notna(v):
        ax.text(
            i,
            v - 18,
            f"{v:.1f}%",
            ha="center",
            va="top",
            fontsize=9,
            color="white",
            rotation=90
        )

# Valores BBP
for i, v in enumerate(df_hist["bbp"]):
    if pd.notna(v):
        ax.text(
            i,
            v + 8,
            f"{v:.1f}%",
            ha="center",
            fontsize=9,
            color="#FE8002"
        )

# Valores MSD
for i, v in enumerate(df_hist["msd"]):
    if pd.notna(v):
        ax.text(
            i,
            v + 1,
            f"{v:.1f}%",
            ha="center",
            fontsize=9,
            color="#E0E0E0"
        )

# Etiquetas
ax.set_ylim(0, 105)
ax.set_xticks(x)
ax.set_xticklabels(
    df_hist["periodo"],
    fontsize=9,
    rotation=0,
    color="white"
)

ax.tick_params(axis="y", colors="white")

# Estilo ejes
ax.spines["left"].set_color("white")
ax.spines["bottom"].set_color("white")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Leyenda
leg = ax.legend(
    loc="lower center",
    bbox_to_anchor=(0.5, -0.4),
    fontsize=8,
    frameon=False,
    ncol=3
)
for text in leg.get_texts():
    text.set_color("white")
plt.subplots_adjust(bottom=0.4)
plt.tight_layout(pad=1.5)

with g:
    st.pyplot(fig, use_container_width=True)
# ================= PRODUCCIÓN / OEE / SCRAP =================
p1,p2,p3 = st.columns([2.2,1.2,1.6])

with p1:
    card(
        "Producción🛠️⚙️",
        f"""Piezas Construidas: {abc_line(A,B,C,'pzs_const')}<br>Defectos acumulados: {abc_line(A,B,C,'defectos_acum')}<br>DPMUs: {abc_line(A,B,C,'dpmus')}""",
        "#FF893B"
    )

with p2: 
    card("OEE✂️",f"""Objetivo: {oee_target if oee_target is not None else "-"}<br>Actual: {oee_actual if oee_actual is not None else "-"}<br>Acum: {oee_acum if oee_acum is not None else "-"}""",
    "#FF893B"
)


with p3:
 st.markdown(
f"""<div style="
background:#FF893B;
border-radius:6px;
padding:10px 12px;
color:#000000;
min-height:140px;
">

<div style="font-size:20px; font-weight:800; margin-bottom:6px;">
SCRAP🚮🗑️
</div>

<div style="font-size:20px; font-weight:700; line-height:1.3;">
<b>Actual:$</b> {abc_line(A,B,C,'scrap_actual')}<br>
<b>Acumulado:$</b> {abc_line(A,B,C,'scrap_acum')}
</div>

</div>""",
        unsafe_allow_html=True
    )

# ================= CENSUS / AUSENTISMO / EHS =================
c1,c2,c3 = st.columns([0.8,2.2,1])

with c1:
    st.markdown(
f"""<div style="
background:#00B7FF;
border-radius:6px;
padding:12px 14px;
color:#000000;
min-height:120px;
display:flex;
flex-direction:column;
">

<div style="font-size:22px; font-weight:800; margin-bottom:6px;">
Census🚻 
</div>

<div style="font-size:18px; font-weight:700; line-height:1.35;">
<b>Total:</b> {census_total}<br>
{abc_line(A,B,C,'census_turno')}
</div>

</div>""",
        unsafe_allow_html=True
    )

with c2:

    card(
        "Ausentismo🧍🏻",
f"""<div style="
display:grid;
grid-template-columns: 1fr 1fr 1fr;
gap:8px;
">

<div>
<b>Injustificado</b>
{abc_line(A,B,C,"aus_injust")}
</div>

<div>
<b>Controlado</b>
{abc_line(A,B,C,"aus_control")}
</div>

<div>
<b>Rotación</b>
{abc_line(A,B,C,"rotacion")}
</div>

<div>
<b>TLO</b>
{abc_line(A,B,C,"tlo")}
</div>

<div>
<b>C-39</b>
{abc_line(A,B,C,"c39")}
</div>

</div>""",
        "#00B7FF"
    )
with c3:
   st.markdown(
f"""<div style="
background:#00B7FF;
border-radius:6px;
padding:12px 14px;
color:#000000;
min-height:120px;
display:flex;
flex-direction:column;
">

<div style="font-size:22px; font-weight:800; margin-bottom:6px;">
Seguridad EHS 🚨
</div>

<div style="font-size:18px; font-weight:700; line-height:1.35;">
<b>Transporte:</b> {abc_line(A,B,C,"ehs_transporte")}<br>
<b>Incidentes:</b> {abc_line(A,B,C,"ehs_incidentes")}
</div>

</div>""",
        unsafe_allow_html=True
    )

# ================= LEER DATOS SEMANALES =================
turno_tabla = st.radio(
    "Turno",
    ["A", "B"],
    horizontal=True
)

def leer_detractores_por_semana(xls, semana_id, turno):
    df = pd.read_excel(xls, "DETRACTORES")

    # Normalizar nombres
    df.columns = df.columns.astype(str).str.strip()

    if turno == "A":
        base_cols = ["semana_id", "shift", "concepto"]
        suf = ""
    else:  # turno B
        base_cols = ["semana_id.1", "shift .1", "concepto.1"]
        suf = ".1"

    # Tomar columnas del turno correspondiente
    cols = base_cols + [
        f"Lunes{suf}", f"%LE TLunes{suf}",
        f"Martes{suf}", f"%LE TMartes{suf}",
        f"Miercoles{suf}", f"%LE Tmiercoles{suf}",
        f"Jueves{suf}", f"%LE TJueves{suf}",
       f"Viernes{suf}", f"%LE TViernes{suf}",
        f"Total Semana{suf}", f"%LE Total{suf}"
    ]

    df_t = df[cols].copy()
    df_t.columns = [
        "semana_id", "shift", "concepto",
        "Lunes", "%LE TLunes",
        "Martes", "%LE TMartes",
        "Miercoles", "%LE Tmiercoles",
        "Jueves", "%LE TJueves",
        "Viernes", "%LE TViernes",
        "Total Semana", "%LE Total"
    ]

    df_t["semana_id"] = df_t["semana_id"].ffill().astype(str).str.strip()
    df_t = df_t[df_t["semana_id"] == semana_id]
    df_t = df_t[df_t["concepto"].notna()]

    df_t = df_t.set_index("concepto")
    return df_t

# -------- TABLA % LE POR CODIGO --------

def leer_le_codigo_por_semana(xls, semana_id, turno):

    df = pd.read_excel(xls, "LE_CODIGO")
    df.columns = df.columns.astype(str).str.strip()

    if turno == "A":
        base = ["semana_id", "shift", "codigo"]
        suf = ""
    else:
        base = ["semana_id.1", "shift.1", "codigo.1"]
        suf = ".1"

    cols = base + [
        f"Lunes{suf}", f"Martes{suf}",
        f"Miercoles{suf}", f"Jueves{suf}",
        f"Viernes{suf}", f"Total Semana{suf}"
    ]

    df_t = df[cols].copy()
    df_t.columns = [
        "semana_id", "shift", "codigo",
        "Lunes", "Martes",
        "Miercoles", "Jueves",
        "Viernes", "Total Semana"
    ]

    df_t["semana_id"] = df_t["semana_id"].ffill().astype(str).str.strip()
    df_t = df_t[df_t["semana_id"] == semana_id]
    df_t = df_t[df_t["codigo"].notna()]

    df_t = df_t.set_index("codigo")

    for col in df_t.columns:
        df_t[col] = pd.to_numeric(df_t[col], errors="coerce")

        df_t[col] = df_t[col].apply(
            lambda x:
                x * 100 if pd.notna(x) and x <= 1 else
                x * 10  if pd.notna(x) else x
        )

    return df_t


    # ---- LE total% ----
df_det_sem = leer_detractores_por_semana(xls, semana_id, turno_tabla)
df_cod_sem= leer_le_codigo_por_semana(xls, semana_id, turno_tabla)

t1, t2 = st.columns([2.6, 1.4])


with t1:

    st.markdown("### Detractores")

    if df_det_sem.empty:
        st.warning("Sin datos")
    else:
        #  QUITAR COLUMNAS NO DESEADAS
        df_show = df_det_sem.drop(
            columns=["semana_id", "shift"],
            errors="ignore"
        )

        def format_det(x, es_pct=False):
            if isinstance(x, (int, float)) and pd.notna(x):
                return f"{x:.1f}%" if es_pct else f"{x:.1f}"
            return x

        formatos = {}
        for col in df_show.columns:
            es_porcentaje = col.lower().startswith("%le")
            formatos[col] = lambda x, p=es_porcentaje: format_det(x, p)

        st.dataframe(
            df_show.style.format(formatos, na_rep="-"),
            use_container_width=True
        )

with t2:

    st.markdown("### % LE por Código")

    if df_cod_sem.empty:
        st.warning("Sin datos")
    else:
        # QUITAR COLUMNAS NO DESEADAS
        df_show = df_cod_sem.drop(
            columns=["semana_id", "shift"],
            errors="ignore"
        )

        def format_pct(x):
            if isinstance(x, (int, float)) and pd.notna(x):
                return f"{x:.1f}%"
            return x

        formatos = {col: format_pct for col in df_show.columns}

        st.dataframe(
            df_show.style.format(formatos, na_rep="-"),
            use_container_width=True
        )

