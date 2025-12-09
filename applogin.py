import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time

# 1. CONFIGURACIÓN INICIAL
st.set_page_config(page_title="Monitor Estudiantil UdeC", layout="wide", page_icon="🎓")


st.markdown("""
<style>
    .stApp { background-color: #F7F9F9; }
    h1, h2, h3 { color: #17202A; font-family: 'Arial', sans-serif; }
    div.stMetric { background-color: white; border: 1px solid #D5DBDB; padding: 10px; border-radius: 5px; }
    /* Estilo para el Login */
    .login-box { border: 1px solid #ddd; padding: 20px; border-radius: 10px; background-color: white; }
</style>
""", unsafe_allow_html=True)


# 2. SISTEMA DE LOGIN (SEGURIDAD)


# Inicializar estado de sesión
if 'logueado' not in st.session_state:
    st.session_state['logueado'] = False

def login():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        # Logo UdeC en login
        st.image("https://fi.udec.cl/wp-content/uploads/2025/05/FI-LOGO-AZ.png", width=300)
        st.title("Acceso Seguro")
        st.markdown("Plataforma de Apoyo Familiar - Facultad de Ingeniería")
        
        with st.form("login_form"):
            usuario = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("Ingresar")
            
            if submit:
                # CREDENCIALES
                if usuario == "modelación" and password == "sistemas":
                    st.success("Acceso Correcto. Cargando sistema...")
                    time.sleep(1)
                    st.session_state['logueado'] = True
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos.")


if not st.session_state['logueado']:
    login()
    st.stop()


# 3. APLICACIÓN PRINCIPAL

# --- CARGAR DATOS ---
@st.cache_data
def cargar_datos():
    try:
        return pd.read_csv("base_app_unificada.csv")
    except FileNotFoundError:
        return None

df = cargar_datos()

# --- SIDEBAR ---
st.sidebar.image("https://fi.udec.cl/wp-content/uploads/2025/05/FI-LOGO-AZ.png", width=200)
st.sidebar.markdown("---")

if st.sidebar.button("Cerrar Sesión"):
    st.session_state['logueado'] = False
    st.rerun()

st.sidebar.header("Panel de Simulación")
st.sidebar.write("Ajuste los valores para simular el estado del alumno.")

# Filtro de Carrera
if df is not None:
    MAPEO_NOMBRES = {
        13072: "Ing. Civil Industrial", 13069: "Ing. Civil", 13070: "Ing. Civil Eléctrica",
        13071: "Ing. Civil Electrónica", 13019: "Ing. Comercial", 13073: "Ing. Civil Informática"
    }
    
    if 'Carrera_ID' in df.columns:
        df['Carrera_ID'] = pd.to_numeric(df['Carrera_ID'], errors='coerce')
        df['Nombre_Visual'] = df['Carrera_ID'].map(MAPEO_NOMBRES)
        df['Nombre_Visual'] = df['Nombre_Visual'].fillna(df['Carrera_ID'].astype(str))
        
        opciones = sorted(df['Nombre_Visual'].unique().astype(str))
        col_filtro = 'Nombre_Visual'
    elif 'Nombre_Carrera' in df.columns:
        opciones = sorted(df['Nombre_Carrera'].unique().astype(str))
        col_filtro = 'Nombre_Carrera'
    else:
        st.error("No se encontró columna de carrera.")
        opciones = []
        col_filtro = None

    if col_filtro:
        carrera_sel = st.sidebar.selectbox("Seleccione Carrera:", opciones)
        df_filtrado = df[df[col_filtro] == carrera_sel]
    else:
        df_filtrado = pd.DataFrame()
else:
    st.error("Error: Falta 'base_app_unificada.csv'")
    df_filtrado = pd.DataFrame()

st.sidebar.markdown("---")

# --- INPUTS ---
input_nem = st.sidebar.number_input("Puntaje NEM", 400, 1000, 600)
input_moti = st.sidebar.slider("Motivación Actual (1-7)", 1, 7, 4)
input_repro = st.sidebar.number_input("Asignaturas Reprobadas", 0, 20, 0)

# --- DASHBOARD PRINCIPAL ---

st.title(f"Tablero de Gestión: {carrera_sel if df is not None else ''}")

# --- CÁLCULOS INTERNOS ---
if not df_filtrado.empty:
    col_dur = next((c for c in df_filtrado.columns if 'duracion' in c.lower()), None)
    duracion = df_filtrado[col_dur].mean() if col_dur else 0
    total_alumnos = len(df_filtrado)
    riesgo_alto = len(df_filtrado[df_filtrado['Nivel_Riesgo'].isin(['Alto', 'Muy Alto'])])
else:
    duracion = 0
    total_alumnos = 0
    riesgo_alto = 0

# --- SECCIÓN A: MÉTRICAS ---
c1, c2, c3 = st.columns(3)
c1.metric("Total Estudiantes", f"{total_alumnos}", "Muestra")
c2.metric("Estudiantes en Riesgo", f"{riesgo_alto}", "Alto / Muy Alto", delta_color="inverse")
c3.metric("Simulación Actual", f"{input_moti}/7", "Nivel Motivación")

st.markdown("---")

# --- SECCIÓN B: GRÁFICOS VISUALES ---

col_g1, col_g2 = st.columns(2)
mapa_colores = {'Bajo':'#27AE60', 'Medio':'#F1C40F', 'Alto':'#E67E22', 'Muy Alto':'#C0392B'}

with col_g1:
    st.subheader("Distribución de Riesgo")
    if not df_filtrado.empty:
        try:
            fig_pie = px.pie(df_filtrado, names='Nivel_Riesgo', 
                             title='Porcentaje de estudiantes según riesgo',
                             color='Nivel_Riesgo',
                             color_discrete_map=mapa_colores,
                             hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
        except Exception as e:
            st.info("No hay datos suficientes.")

with col_g2:
    st.subheader("Distribución de Motivación")
    if not df_filtrado.empty:
        try:
            fig_hist = px.histogram(df_filtrado, x="Motivacion_Actual", 
                                    title="Comparativa con la carrera",
                                    nbins=7, range_x=[0.5, 7.5],
                                    color_discrete_sequence=['#2980B9'])
            fig_hist.add_vline(x=input_moti, line_width=2, line_dash="dash", line_color="#C0392B")
            fig_hist.add_annotation(x=input_moti, y=0, text="Alumno", showarrow=True, arrowhead=2, ay=-40, font=dict(color="#C0392B"))
            fig_hist.update_layout(xaxis_title="Nivel (1-7)", yaxis_title="Cantidad")
            st.plotly_chart(fig_hist, use_container_width=True)
        except:
            st.info("No hay datos suficientes.")

st.markdown("---")

# --- SECCIÓN C: DIAGNÓSTICO Y MAPA ---

col_diag, col_scatter = st.columns([1, 2])

with col_diag:
    st.subheader("Diagnóstico Personalizado")
    riesgo_detectado = False
    if input_moti < 4:
        st.error("ALERTA MOTIVACIONAL")
        st.write("La motivación es crítica. Se sugiere intervención.")
        riesgo_detectado = True
    elif input_repro > 1:
        st.warning("ALERTA ACADÉMICA")
        st.write("Reprobación sobre el estándar.")
        riesgo_detectado = True
    
    if not riesgo_detectado:
        st.success("ESTADO ESTABLE")
        st.write("El estudiante se encuentra en buenos rangos.")

    if duracion > 0:
        st.info(f"Contexto: La duración promedio real es de {duracion:.1f} semestres.")

with col_scatter:
    st.subheader("Mapa de Ubicación")
    st.write("Rendimiento (NEM) vs. Motivación")
    if not df_filtrado.empty:
        try:
            fig_sc = px.scatter(df_filtrado, x="NEM", y="Motivacion_Actual", 
                                color="Nivel_Riesgo", 
                                title="Generación (Puntos) vs. Alumno (Estrella)",
                                color_discrete_map=mapa_colores,
                                hover_data=["Confianza_Academica"])
            fig_sc.add_trace(go.Scatter(
                x=[input_nem], y=[input_moti],
                mode='markers',
                marker=dict(color='black', size=15, symbol='star', line=dict(width=1, color='white')),
                name='ALUMNO'
            ))
            st.plotly_chart(fig_sc, use_container_width=True)
        except:
            st.info("Faltan datos para generar el mapa.")