import datetime as dt
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import os
import matplotlib.pyplot as plt
import signal
import sys
#if "start" not in st.session_state:
 #   st.session_state.start = False

#if not st.session_state.start:
    #st.markdown(
       # """
       # <h1 style="text-align:center;">Dashboard Producción</h1>
        #<h3 style="text-align:center;">Semana Actual</h3>
        #<br><br>
        #""",
     #   unsafe_allow_html=True
    #)

    #col1, col2, col3 = st.columns([1,2,1])
    #with col2:
   #     if st.button("▶ Iniciar Dashboard", use_container_width=True):
  #          st.session_state.start = True

 #   st.stop()   # ⛔ no carga nada más

def resource_path(relative_path):
    """Obtiene la ruta correcta tanto en desarrollo como en .exe"""
    try:
        base_path = sys._MEIPASS  # PyInstaller temp folder
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
LOGO_PATH = resource_path("aptiv_logo.png")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(BASE_DIR, "aptiv_logo.png")
# Excel según plataforma
archivo = "dashboard_tier_data_TESLA.xlsx"  # por defecto, cambia según plataforma


plt.rcParams.update({
    "figure.dpi": 140,
    "font.size": 7
})

# ================= CONFIG =================
st.set_page_config(page_title="TIER Dashboard", layout="wide")

st.markdown("""
<style>
.block-container {
    padding-top: 2.8rem;
}
</style>
""", unsafe_allow_html=True)

# ================= HELPERS =================
def get_val(row, col, suf=""):
    try:
        v = row[col]
        return "-" if pd.isna(v) else f"{v}{suf}"
    except Exception:
        return "-"

def card(title, body, h=60, bg="#2FFF05F8"):
    html = f"""
    <div style="
        background:{bg};
        padding:10px;
        border-radius:8px;
        font-size:22px;
        height:{h}px;
        box-shadow:0 1px 3px rgba(0,0,0,.15);
    ">
        <b>{title}</b><br>{body}
    </div>
    """
    components.html(html, height=h+20)

def abc_line(A, B, C, col, suf=""):
    return (
        f"TA: {get_val(A,col,suf)} &nbsp;&nbsp; "
        f"TB: {get_val(B,col,suf)} &nbsp;&nbsp; "
        f"TC: {get_val(C,col,suf)}"
    )



# ================= LECTURA DETRACTORES POR SEMANA =================

def leer_detractores_por_semana(xls, semana_id):
    df = pd.read_excel(xls, "DETRACTORES")

    # Usar directamente la columna real
    if "semana_id" not in df.columns:
        st.error("No se encontró la columna 'semana_id' en DETRACTORES")
        return pd.DataFrame()

    # Rellenar hacia abajo por bloques
    df["semana_id"] = df["semana_id"].ffill().astype(str).str.strip()

    # Filtrar semana
    df_sem = df[df["semana_id"] == semana_id].copy()
    if df_sem.empty:
        return pd.DataFrame()

    # Usar la columna de concepto (segunda columna)
    col_concepto = df.columns[1]

    df_sem = df_sem.rename(columns={col_concepto: "Concepto"})
    df_sem = df_sem.set_index("Concepto")
    # Quitar columna tecnica
    df_sem = df_sem.drop(columns=["semana_id"])

    nuevas_columnas = []
    ultimo_dia = None

    for col in df_sem.columns:
        if col == "%":
            nuevas_columnas.append(f"% {ultimo_dia}")
        else:
            nuevas_columnas.append(col)
            ultimo_dia = col

    df_sem.columns = nuevas_columnas

    cols_orden = [
        "Lunes", "%LE TLunes",
        "Martes", "%LE TMartes",
        "Miercoles", "%LE Tmiercoles",
        "Jueves", "%LE TJueves",
        "Viernes", "%LE TViernes",
        "Total Semana", "%LE Total"
    ]
    cols_presentes = [c for c in cols_orden if c in df_sem.columns]
    df_sem = df_sem[cols_presentes]

    return df_sem

# ================= LECTURA % LE POR CODIGO POR SEMANA =================

def leer_le_codigo_por_semana(xls, semana_id):
    df = pd.read_excel(xls, "LE_CODIGO")

    if "semana_id" not in df.columns:
        st.error("No se encontró la columna 'semana_id' en LE_CODIGO")
        return pd.DataFrame(), pd.DataFrame()

    df["semana_id"] = df["semana_id"].ffill().astype(str).str.strip()

    df_sem = df[df["semana_id"] == semana_id].copy()
    if df_sem.empty:
        return pd.DataFrame(), pd.DataFrame()

    col_codigo = df.columns[1]

    df_sem = df_sem.rename(columns={col_codigo: "Codigo"})
    df_sem = df_sem.set_index("Codigo")
    df_sem = df_sem.drop(columns=["semana_id"])
    cols_orden = [
        "Lunes",
        "Martes",
        "Miercoles", 
        "Jueves", 
        "Viernes", 
        "Total Semana", 
    ]
    cols_presentes = [c for c in cols_orden if c in df_sem.columns]
    df_sem = df_sem[cols_presentes]

    return df_sem, pd.DataFrame()

# ================= DATA PATH =================
#RUTA = r"C:\Users\24tjo8\OneDrive - Aptiv\Dashboard"
#EXCEL = os.path.join(RUTA, archivo)
#EXCEL_TESLA = os.path.join(RUTA, "dashboard_tier_data_TESLA.xlsx")
#EXCEL_STELLANTIS = os.path.join(RUTA, "dashboard_tier_data_STELLANTIS.xlsx")
#BASE_DIR = os.path.dirname(os.path.abspath(__file__))
#LOGO_PATH = os.path.join(RUTA, "aptiv_logo.png")
# ================= HEADER =================
h1, h2, h3, h4 = st.columns([1.2, 1.2, 1, 1])

with h1:
    plataforma = st.selectbox(
        "Plataforma",
        ["TESLA", "STELLANTIS"],
        label_visibility="collapsed"
    )

archivo = (
    "dashboard_tier_data_TESLA.xlsx"
    if plataforma == "TESLA"
    else "dashboard_tier_data_STELLANTIS.xlsx"
)

EXCEL = os.path.join(BASE_DIR, archivo)
xls = pd.ExcelFile(EXCEL)

df = pd.read_excel(xls, "TIER_MAIN")
df_cod = pd.read_excel(xls, "LE_CODIGO")
df_det = pd.read_excel(xls, "DETRACTORES")

# ================= NORMALIZE =================
df['date'] = pd.to_datetime(df['date'], errors='coerce')
df["shift"] = df["shift"].astype(str).str.upper().str.strip()

min_date = df['date'].dropna().min().date()
max_date = df['date'].dropna().max().date()
today=dt.date.today()

if min_date <= today <= max_date:
    default_date = today
else:
    default_date = max_date

with h2:

    fecha= st.date_input(
    "Fecha",
    min_value=min_date,
    max_value=max_date,
    value=default_date,  label_visibility="collapsed"
)
with h4:
        if st.button("🚪 Salir del sistema"): os.kill(os.getpid(), signal.SIGTERM)
# ================= SEMANA DESDE FECHA =================
def obtener_semana_id(fecha):
    anio, semana, _ = fecha.isocalendar()
    return f"{anio}-W{semana:02d}"

semana_id = obtener_semana_id(fecha)

# DEBUG (opcional - puedes quitar después)
st.write("Semana calculada:", semana_id)

with h3:
     st.image(LOGO_PATH, width=180)

st.markdown(f"### {plataforma} – TIER GENERAL | {fecha}")


# ================= FILTER DAY =================
df_dia = df[df.date.dt.date == fecha]
if df_dia.empty:
    st.stop()

A = df_dia[df_dia["shift"] == "A"].iloc[0] if not df_dia[df_dia["shift"]=="A"].empty else None
B = df_dia[df_dia["shift"] == "B"].iloc[0] if not df_dia[df_dia["shift"]=="B"].empty else None
C = df_dia[df_dia["shift"] == "C"].iloc[0] if not df_dia[df_dia["shift"]=="C"].empty else None

#row = B if B is not None else df_dia.iloc[0]

def fila_diaria(df_dia):
    fila = {}

    # Sumar
    for c in ["pzs_const", "defectos_acum", "dpmus", "scrap_acum"]:
        fila[c] = df_dia[c].sum(skipna=True)

    # Tomar último valor válido
    for c in [
        "le_dia_actual", "le_dia_forecast",
        "ef_mes_actual", "ef_mes_forecast", "defectos_acum", "dpmus",
        "oee_actual", "oee_acum", "oee_target",
        "scrap_actual", "scrap_acum", "census_total"
    ]:
        fila[c] = df_dia[c].dropna().iloc[-1] if not df_dia[c].dropna().empty else None

    return fila

row = fila_diaria(df_dia)

def quejas_target_diario(df_dia):
    if "quejas_target" not in df_dia.columns:
        return None
    s = df_dia["quejas_target"].dropna()
    return s.iloc[-1] if not s.empty else None

quejas_target_dia = quejas_target_diario(df_dia)

# ================= HISTORY =================
hist = (
    df[df.date.dt.date <= fecha]
    .sort_values("date")
    .tail(6)
)


# ================= FILA 1 =================
c1,c2,c3,c4 = st.columns([1, 1, 1, 1])
with c1: card("Desempeño Primera Hora", abc_line(A,B,C,"des_primera_hora","%"))
with c2: card("Desempeño Última Hora", abc_line(A,B,C,"des_ultima_hora","%"))
with c3: card("% LE por Turno", abc_line(A,B,C,"le_turno","%"))
with c4: card("Eficiencia del dia", f"Actual: {get_val(row,'le_dia_actual','%')} |  Forecast: {get_val(row,'le_dia_forecast','%')}" )

# ================= FILA 2 =================
left, right = st.columns([1.6, 2.4])

# ---------- COLUMNA IZQUIERDA ----------
with left:

    # Eficiencia del Mes
    card(
        "Eficiencia del Mes", f"Actual: {get_val(row,'ef_mes_actual','%')} |  Forecast: {get_val(row,'ef_mes_forecast','%')}"
    )

    # Quejas

    qcols = ["quejas_cuales", "quejas_codigo"]


    if "quejas_codigo" in df_dia.columns:

        qdf = df_dia[
            df_dia["quejas_codigo"]
            .notna()
            & (df_dia["quejas_codigo"].astype(str).str.strip() != "")
        ][["quejas_cuales", "quejas_codigo"]]

        total_quejas = len(qdf)

        qtxt = (
            "_Sin quejas_"
            if qdf.empty
            else "\n".join(
                f"<br>• {r.quejas_cuales} {r.quejas_codigo}"
                for _, r in qdf.iterrows()
            )
        )
    else:
        total_quejas = 0
        qtxt = "_Sin quejas_"



    card(
        "Quejas",
        f"Target: {quejas_target_dia if quejas_target_dia is not None else '-'}\n"
        f"Actual: {total_quejas}\n{qtxt}",
        h=160,
        bg="#E6FF04"
    )


    # Producción + Target / Acum
    p1, p2, p3 = st.columns([2, 1.3, 1])

    with p1:
        card(
            "Producción",
            f"Piezas Construidas: {get_val(row,'pzs_const')}<br>"
            f"Defectos acumulados: {get_val(row,'defectos_acum')}<br>"
            f"DPMUs: {get_val(row,'dpmus')}",  bg="#FF893B",
            h=109
        )

    with p2:
        
        card(
            "OEE", f"""<span style="font-size:20px;">
            Target: {get_val(row,'oee_target')}<br>
            Actual: {get_val(row,'oee_actual')}<br>
            Acum: {get_val(row,'oee_acum')}<br>, </span>""", bg="#FF893B",
            h=109
        )
    with p3:
        
        card(
            "SCRAP",
            f"""<span style="font-size:20px;">
            Actual: {get_val(row,'scrap_actual')}<br>
            Acum: {get_val(row,'scrap_acum')}</span>""", bg="#FF893B",
            h=109
        )
# ---------- COLUMNA DERECHA (MSD) ----------
with right:
    SHEET_HIST="LE_HISTORICO"
    df_raw = pd.read_excel(xls, SHEET_HIST)

    # Primera columna = KPI (Actual / BBP / MSD)
    df_raw = df_raw.rename(columns={df_raw.columns[0]: "KPI"})
    df_raw = df_raw.set_index("KPI")

    # Transformar a formato grafica
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

    def tipo_periodo(p):
        p = str(p).lower()
        if p.startswith("wk"):
            return "semana"
        elif len(p) <= 4 and p.isalpha():
            return "mes"
        else:
            return "dia"

    df_hist["tipo"] = df_hist["periodo"].apply(tipo_periodo)

    color_map = {
        "mes": "#4ECF04",      # verde fuerte
        "semana": "#00CC63",   # mismo verde
        "dia": "#02F7FF"       # verde más claro
    }

    hatch_map = {
        "mes": "",
        "semana": "///",       # 👈 aquí se distinguen
        "dia": ""
    }

    # Limpiar porcentajes y convertir a numerico

    for c in ["actual", "bbp", "msd"]:
        df_hist[c] = (
        pd.to_numeric(df_hist[c], errors="coerce") * 100 )
        df_hist[c] = pd.to_numeric(df_hist[c], errors="coerce")

    # ================= GRAFICA =================
    fig, ax = plt.subplots(figsize=(4.8, 1.6))
    fig.patch.set_facecolor("#000000")
    ax.set_facecolor("#000000")

    x = range(len(df_hist))

    # Barras - Actual
   
    for i, row in df_hist.iterrows():
        ax.bar(
            i,
            row["actual"],
            width=0.6,
            color=color_map[row["tipo"]],
            hatch=hatch_map[row["tipo"]],
            label="Actual" if i == 0 else ""
        )

    for i in range(1, len(df_hist)):
        if df_hist.loc[i, "tipo"] != df_hist.loc[i - 1, "tipo"]:
            ax.axvline(
                i - 0.5,
                color="#5A5757",
                linewidth=0.8,
                linestyle="--"
            )

    # Linea MSD
    ax.plot(
        x,
        df_hist["msd"],
        "--o",
        color="#A7A7A7",
        markersize=3,
        label="MSD"
    )

    # Linea BBP
    ax.plot(
        x,
        df_hist["bbp"],
        "-o",
        color="#17C720",
        markersize=3,
        label="BBP"
    )

    # Etiquetas dentro de barras
    for i, v in enumerate(df_hist["actual"]):
        if pd.notna(v):
            ax.text(
                i,
                v - 2,
                f"{v:.2f}%",
                ha="center",
                va="top",
                color="white",
                fontsize=5,
                rotation=90
            )

    # Etiquetas sobre lineas
    for i, v in enumerate(df_hist["bbp"]):
        if pd.notna(v):
            ax.text(
                i,
                v + 0.4,
                f"{v:.2f}%",
                fontsize=6,
                ha="center",
                color="#2BE034"
            )

    for i, v in enumerate(df_hist["msd"]):
        if pd.notna(v):
            ax.text(
                i,
                v + 0.4,
                f"{v:.2f}%",
                fontsize=6,
                ha="center",
                color="#B8B2B2"
            )

    # Ejes y estilo
    ax.set_ylim(0, 102)
    ax.set_xticks(x)
    ax.set_xticklabels(df_hist["periodo"], fontsize=7)
    ax.set_yticks([0, 101, 50,10])
    ax.tick_params(axis="y", labelsize=7)
    ax.spines["left"].set_color("#FFFFFF")
    ax.tick_params(axis="y", colors="#FFFFFF")
    ax.yaxis.label.set_color("#FFFFFF")
    ax.spines["bottom"].set_color("#FFFFFF")
    ax.tick_params(axis="x", colors="#FFFFFF")
    ax.xaxis.label.set_color("#FFFEFE")



    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)

    leg = ax.legend(
        loc="upper right",
        bbox_to_anchor=(0.5, -0.25),
        fontsize=7,
        frameon=False,
        ncol=3
    )

    for text in leg.get_texts():
        text.set_color("#FFFFFF")

    plt.tight_layout(pad=0.3)
    st.pyplot(fig, use_container_width=False)

left, right = st.columns([1.6, 2.4])


# -------- COLUMNA DERECHA (HISTORICO LE) --------
with right:

    SHEET_HIST = "LE_HISTORICO"

    # Verificar que la hoja exista en el archivo actual (TESLA o STELLANTIS)
    if SHEET_HIST not in xls.sheet_names:
        st.error(
            f"No existe la hoja '{SHEET_HIST}' en el archivo "
            f"{os.path.basename(EXCEL)}"
        )
        st.stop()
# ================= FILA 3 =================

def census_diario(df_dia):
    if "census_total" not in df_dia.columns:
        return None
    s = df_dia["census_total"].dropna()
    return s.iloc[-1] if not s.empty else None

census_total_dia = census_diario(df_dia)

def card(title=6, *lines, h=100, bg="#00B7FF"):
    st.markdown(
        f"""
        <div style="background-color:{bg}; padding:15px; border-radius:8px; font-size:17px;">
            <h4>{title}</h4>  
            {'| '.join(lines)}
        </div>
        """,
        unsafe_allow_html=True
    )

c1,c2,c3 = st.columns([1, 2, 1])

with c1: card( "Census",  f"""<span style="font-size:20px;"> Total: {census_total_dia or '-'}\n | {abc_line(A,B,C,'census_turno')}</span""")
with c2: card("Ausentismo", f"<b>Injustificado:</b> {abc_line(A,B,C,"aus_injust")}",f"<b>Controlado:</b> {abc_line(A,B,C,"aus_control")}",f"<br><b>Rotacion:</b> {abc_line(A,B,C,"rotacion")}",f"<b>TLO: </b>{abc_line(A,B,C,"tlo")}",f"<b>C-39:</b> {abc_line(A,B,C,"c39")}")
with c3: card("Seguridad EHSS", f"Transporte: {abc_line(A,B,C,"ehs_transporte")}",f"Incidentes: {abc_line(A,B,C,"ehs_incidentes")}")

# ================= LEER DATOS SEMANALES =================
df_det_sem = leer_detractores_por_semana(xls, semana_id)
df_cod_sem, df_le_total = leer_le_codigo_por_semana(xls, semana_id)

# ================= FILA 4 =================# =================
# ----- TITULOS -----
t_l, t_r = st.columns([2.6, 1.4])

with t_l:
    st.markdown("### Detractores del Día")

with t_r:
    st.markdown("### % LE por Código")


t1, t2 = st.columns([2.6, 1.4])

# -------- TABLA DETRACTORES --------


with t1:
    if df_det_sem.empty:
        st.warning("No hay datos para esta semana")
    else:
        pct_cols = [c for c in df_det_sem.columns if c.startswith("%LE")]
        num_cols = [
            c for c in df_det_sem.columns
            if c not in pct_cols and df_det_sem[c].dtype != "object"
        ]

        formato = {}
        formato.update({c: "{:.1%}" for c in pct_cols})
        formato.update({c: "{:,.0f}" for c in num_cols})

        st.dataframe(
            df_det_sem.style.format(formato),
            height=260,
            use_container_width=True
        )

# -------- TABLA % LE POR CODIGO --------

with t2:

    if df_cod_sem.empty:
        st.warning("No hay datos para esta semana")
    else:
        num_cols = [
            c for c in df_cod_sem.columns
            if c != "Codigo"
        ]

        st.dataframe(
            df_cod_sem.style.format({c: "{:.1%}" for c in num_cols}),
            height=240,
            use_container_width=True
        )

    # ---- LE total% ----

    if not df_le_total.empty:
        st.markdown("**LE total%**")
        st.dataframe(
            df_le_total.style.format({
                "%LE Total": "{:.1%}"
            }),
            use_container_width=True
        )


