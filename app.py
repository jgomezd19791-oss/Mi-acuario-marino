import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la interfaz web
st.set_page_config(page_title="Monitor de Acuario Marino", layout="wide", page_icon="🐠")
st.title("🐠 Monitor de Acuario Marino — Panel Dinámico")

# === 🛠️ CONFIGURACIÓN DE TU NUEVA HOJA EN LA CUENTA LIMPIA ===
id_documento = "1nD1guqzPzwfcSgLnUrTk0qeoZm9tRDOHjiI8IHoGhzY"
id_pestana = "1568791642"  # Tu nuevo GID de pestaña
# ======================================================

url_definitiva = f"https://docs.google.com/spreadsheets/d/{id_documento}/gviz/tq?tqx=out:csv&gid={id_pestana}"

try:
    # 1. Leemos el archivo limpio desde el principio
    df = pd.read_csv(url_definitiva)
    
    # 2. Limpieza estricta de nombres de columnas
    df.columns = df.columns.str.strip()
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

    # Identificar la columna de Fecha automáticamente
    col_fecha = [c for c in df.columns if 'fecha' in c.lower()]
    if col_fecha:
        df.rename(columns={col_fecha[0]: 'Fecha'}, inplace=True)
    
    if 'Fecha' in df.columns:
        df['Fecha'] = df['Fecha'].astype(str).str.strip()
        # Descartamos filas completamente vacías o decorativas
        df = df[df['Fecha'] != 'nan']
        df = df[df['Fecha'] != '']

    # Columnas que sabemos que son exclusivamente numéricas (parámetros)
    columnas_parametros = [
        c for c in df.columns 
        if any(p in c.lower() for p in ['kh', 'mg', 'ca', 'po', 'salinidad'])
    ]

    # 3. Procesar las columnas con comas directamente
    for col in df.columns:
        if col in columnas_parametros:
            # Convertimos a texto, reemplazamos tus comas por puntos para Python, y forzamos número
            df[col] = df[col].astype(str).str.replace(',', '.', regex=False).str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce')
        else:
            # Para aditivos, dosis y notas limpiamos textos vacíos
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace('nan', '')

    # Quitar filas que se hayan quedado completamente vacías
    df = df.dropna(subset=['Fecha'])

    st.success("📊 ¡Conectado al registro de tu acuario marino con éxito!")

    # --- MÉTRICAS DE LOS ÚLTIMOS VALORES (KPIs) ---
    def buscar_col(keywords):
        for c in df.columns:
            if any(k in c.lower() for k in keywords):
                return c
        return None

    c_kh = buscar_col(['kh'])
    c_mg = buscar_col(['mg'])
    c_ca = buscar_col(['ca'])
    c_po4 = buscar_col(['po'])
    c_sal = buscar_col(['salinidad'])
    
    if c_kh and not df.dropna(subset=[c_kh]).empty:
        st.subheader("📌 Estado de la última medición")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        # Obtenemos la última fila registrada
        ultima_medicion = df.iloc[-1]
        
        with col1:
            val_kh = f"{ultima_medicion[c_kh]} dKH" if pd.notna(ultima_medicion[c_kh]) else "N/A"
            st.metric(label="KH (Ideal: 7-11)", value=val_kh)
        with col2:
            val_mg = f"{ultima_medicion[c_mg]} ppm" if c_mg and pd.notna(ultima_medicion[c_mg]) else "N/A"
            st.metric(label="Magnesio (Ideal: 1250-1350)", value=val_mg)
        with col3:
            val_ca = f"{ultima_medicion[c_ca]} ppm" if c_ca and pd.notna(ultima_medicion[c_ca]) else "N/A"
            st.metric(label="Calcio (Ideal: 400-450)", value=val_ca)
        with col4:
            # Buscamos el último PO4 real que no sea nulo en el histórico para evitar huecos en los KPIs
            df_val_po4 = df.dropna(subset=[c_po4]) if c_po4 else pd.DataFrame()
            val_po4_num = df_val_po4.iloc[-1][c_po4] if not df_val_po4.empty else None
            val_po4 = f"{val_po4_num} ppm" if val_po4_num is not None else "N/A"
            st.metric(label="Fosfatos (Ideal: 0-0.05)", value=val_po4)
        with col5:
            val_sal = f"{ultima_medicion[c_sal]} ppt" if c_sal and pd.notna(ultima_medicion[c_sal]) else "N/A"
            st.metric(label="Salinidad (Ideal: 34-36)", value=val_sal)

    # --- FILTRO Y GRÁFICA INTERACTIVA ---
    st.markdown("---")
    st.subheader("📈 Evolución Histórica de Parámetros")
    
    if columnas_parametros:
        parametro_seleccionado = st.selectbox("Selecciona el parámetro a analizar:", columnas_parametros)
        
        df_limpio_grafica = df.dropna(subset=[parametro_seleccionado])
        if not df_limpio_grafica.empty:
            fig = px.line(
                df_limpio_grafica, 
                x='Fecha', 
                y=parametro_seleccionado, 
                markers=True,
                title=f"Evolución temporal de {parametro_seleccionado}",
                labels={parametro_seleccionado: parametro_seleccionado, "Fecha": "Fecha de Medición"}
            )
            fig.update_layout(hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)

    # --- TABLA INTERACTIVA ---
    st.markdown("---")
    st.subheader("📋 Historial completo de mediciones y notas")
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Hubo un problema al procesar los parámetros. Detalles: {e}")
