import pandas as pd
import google.generativeai as genai
import os
import ast
import re
import markdown2
import streamlit as st
import plotly.express as px  # Para gráficos interactivos

# Configuración de la página (DEBE SER LA PRIMERA LÍNEA DE STREAMLIT)
st.set_page_config(page_title="Análisis de Empresas", layout="wide")

# Habilitar el desplazamiento vertical
st.markdown(
    """
    <style>
    .stApp {
        overflow-y: auto;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Obtener la clave API desde una variable de entorno
GEMINI_API_KEY = "AIzaSyAd-6n4h2Y0jUtdD75CH3xt1eke2pu4qYk"
if not GEMINI_API_KEY:
    st.error("No se encontró la variable de entorno GEMINI_API_KEY.")
    st.stop()

# Configuración de la API Gemini
genai.configure(api_key=GEMINI_API_KEY)

# -----------------------------------------------------------------------------
# FUNCIONES AUXILIARES
# -----------------------------------------------------------------------------

def call_ia_model(data_chunk, prompt, model_name="gemini-1.5-flash"):
    """
    Llama a la IA enviando un prompt junto con el trozo de datos (data_chunk).
    Devuelve el texto completo de la respuesta.
    """
    try:
        if isinstance(data_chunk, pd.DataFrame):
            data_str = data_chunk.to_csv(index=False)
        else:
            data_str = str(data_chunk)

        full_prompt = f"{prompt}\n\nDatos:\n{data_str}"

        model = genai.GenerativeModel(model_name)
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"


def extraer_lista_desde_respuesta(respuesta):
    """
    Usa regex para encontrar la primera lista de diccionarios en formato Python dentro de la respuesta.
    """
    try:
        match = re.search(r"\[.*\]", respuesta, re.DOTALL)
        if match:
            return match.group(0)  # Extrae el texto que representa la lista
        else:
            return None
    except Exception:
        return None


def procesar_respuesta_ia(respuesta):
    """
    Convierte la cadena extraída (lista de diccionarios en formato Python) a un objeto Python.
    Retorna la lista de diccionarios o None en caso de error.
    """
    try:
        lista_str = extraer_lista_desde_respuesta(respuesta)
        if not lista_str:
            return None

        datos = ast.literal_eval(lista_str)
        if isinstance(datos, list) and all(isinstance(d, dict) for d in datos):
            return datos
        else:
            return None
    except Exception:
        return None


def analizar_en_lotes(df_original, prompt, chunk_size=50):
    """
    Procesa el DataFrame 'df_original' en lotes de tamaño 'chunk_size'.
    Devuelve un DataFrame con las columnas ['ID', 'Puntuación', 'Criterios'].
    """
    resultados_globales = []

    for i in range(0, len(df_original), chunk_size):
        df_chunk = df_original.iloc[i : i + chunk_size].copy()

        # Llamada a la IA para el chunk
        respuesta = call_ia_model(df_chunk, prompt)

        # Procesamos la respuesta
        datos_ia = procesar_respuesta_ia(respuesta)
        if datos_ia:
            resultados_globales.extend(datos_ia)
        else:
            # Si falla, puedes implementar algún reintento o logging
            st.warning(f"No se pudieron procesar los registros de {i} a {i+chunk_size}.")
            continue

    # Convertimos todos los resultados en un DataFrame
    df_resultados = pd.DataFrame(resultados_globales)
    # Filtra las columnas que quieras usar
    if not df_resultados.empty:
        df_resultados = df_resultados[["ID", "Puntuación", "Criterios"]]
    return df_resultados


# -----------------------------------------------------------------------------
# FUNCIÓN PARA GENERAR INFORME EJECUTIVO (LA DE TU CÓDIGO ORIGINAL)
# -----------------------------------------------------------------------------

def generar_informe(df):
    # Calcular métricas clave
    total_empresas = len(df)
    alto_potencial = df[df["Puntuación_y"] >= 7]
    medio_potencial = df[(df["Puntuación_y"] >= 5) & (df["Puntuación_y"] < 7)]
    bajo_potencial = df[df["Puntuación_y"] < 5]

    porcentaje_alto_potencial = (len(alto_potencial) / total_empresas) * 100 if total_empresas > 0 else 0
    puntuacion_promedio = df["Puntuación_y"].mean() if total_empresas > 0 else 0

    # Crear el resumen ejecutivo en Markdown
    informe_md = (
        "# Informe Ejecutivo de Análisis de Empresas\n\n"
        "## Resumen General\n"
        f"- **Total de empresas analizadas**: {total_empresas}\n"
        f"- **Empresas de Alto Potencial (Puntuación >= 7)**: {len(alto_potencial)} ({porcentaje_alto_potencial:.2f}%)\n"
        f"- **Empresas de Medio Potencial (Puntuación 5-6)**: {len(medio_potencial)}\n"
        f"- **Empresas de Bajo Potencial (Puntuación < 5)**: {len(bajo_potencial)}\n"
        f"- **Puntuación promedio**: {puntuacion_promedio:.2f}\n\n"
        "## Análisis por Sectores\n"
    )

    # Agregar análisis por sector
    if total_empresas > 0:
        for sector, grupo in df.groupby("Categoría"):
            informe_md += (
                f"- **{sector}**: {len(grupo)} empresas, "
                f"Puntuación promedio: {grupo['Puntuación_y'].mean():.2f}\n"
            )

    return informe_md

# -----------------------------------------------------------------------------
# APLICACIÓN STREAMLIT
# -----------------------------------------------------------------------------

st.title("Análisis de Empresas Colombianas")
st.write("Esta aplicación analiza empresas colombianas y genera una puntuación de prospecto usando IA.")

# Cargar el archivo CSV
archivo = "empresas_colombia_2.csv"
if os.path.exists(archivo):
    df = pd.read_csv(archivo, quotechar='"', delimiter=",", encoding="utf-8-sig")

    # Mostrar el DataFrame original en un menú expandible
    with st.expander("Ver Datos Originales"):
        st.dataframe(df)

    # Prompt específico para el análisis
    prompt = (
        "Eres un analista de negocios especializado en el sector industrial. Tu tarea es evaluar el potencial "
        "de cada empresa como cliente para una compañía que vende repuestos industriales, bandas transportadoras, "
        "cintas, estribadores, carretillas, lubricantes, grasas grado alimenticio y otros productos relacionados "
        "con logística y transmisión de potencia. \n"
        "Anteriormente, la empresa ha vendido a empresas como Colanta, productoras de café, productoras de productos "
        "alimenticios, canteras, productoras de pinturas, entre otros. La idea es llegar a empresas grandes que puedan "
        "generar tickets considerables.\n"
        "Para cada empresa, asigna una puntuación del 1 al 10, donde 1 es el peor prospecto y 10 el mejor. Considera:\n"
        "- Categoría de la empresa.\n"
        "- Actividad principal.\n"
        "- Productos que se pueden ofrecer.\n"
        "- Relevancia para el sector industrial.\n"
        "Responde con una lista de diccionarios en formato Python, donde cada diccionario tenga:\n"
        "- 'ID': El ID de la empresa.\n"
        "- 'Nombre': El nombre de la empresa.\n"
        "- 'Puntuación': La puntuación asignada (1-10).\n"
        "- 'Criterios': Los criterios de puntuación.\n"
        "Ejemplo:\n"
        "[{'ID': '123', 'Nombre': 'Empresa A', 'Puntuación': 8, 'Criterios': 'Buena relevancia...'}, ...]"
    )

    # Botón para ejecutar el análisis
    if st.button("Generar Puntuación"):
        # Llamar a la IA en lotes
        st.info("Procesando registros en lotes, por favor espera...")
        df_lotes = analizar_en_lotes(df, prompt, chunk_size=50)  # Ajusta chunk_size según tus necesidades

        if not df_lotes.empty:
            # Fusionar los resultados con el DataFrame original
            df = df.merge(df_lotes, on="ID", how="left")

            # Mostrar el DataFrame actualizado
            with st.expander("Ver Datos Actualizados con Puntuación"):
                st.dataframe(df)

            # Generar el informe ejecutivo en Markdown
            informe_md = generar_informe(df)

            # Mostrar el informe en forma de KPIs
            st.markdown("## KPIs del Informe")

            col1, col2, col3 = st.columns(3)
            col1.metric("Total de Empresas", len(df))
            col2.metric("Empresas de Alto Potencial", len(df[df["Puntuación_y"] >= 7]))
            col3.metric("Puntuación Promedio", f"{df['Puntuación_y'].mean():.2f}")

            # Crear pestañas para organizar el contenido
            tab1, tab2 = st.tabs(["Informe", "Gráficas"])

            with tab1:
                st.markdown("## Informe ")
                st.markdown(informe_md)

            with tab2:
                st.markdown("## Gráficas de Análisis")

                # Gráfica 1: Empresas segmentadas por potencial
                st.markdown("### Empresas Segmentadas por Potencial")
                segmentos = {
                    "Alto Potencial": len(df[df["Puntuación_y"] >= 7]),
                    "Medio Potencial": len(df[(df["Puntuación_y"] >= 5) & (df["Puntuación_y"] < 7)]),
                    "Bajo Potencial": len(df[df["Puntuación_y"] < 5]),
                }
                df_segmentos = pd.DataFrame(list(segmentos.items()), columns=["Segmento", "Cantidad"])
                fig1 = px.bar(df_segmentos, x="Segmento", y="Cantidad", color="Segmento", text="Cantidad")
                st.plotly_chart(fig1, use_container_width=True)

                # Gráfica 2: Productos ofertados a empresas de medio y alto potencial
                st.markdown("### Productos Ofertados a Empresas de Medio y Alto Potencial")

                lista_productos = [
                    "Bandas transportadoras",
                    "Carretillas",
                    "Lubricantes",
                    "Cintas",
                    "Estribadores"
                ]

                df_filtrado = df[df["Puntuación_y"] >= 5]
                conteo_productos = {producto: 0 for producto in lista_productos}

                for _, fila in df_filtrado.iterrows():
                    criterios_lower = str(fila["Criterios"]).lower()
                    for producto in lista_productos:
                        if producto.lower() in criterios_lower:
                            conteo_productos[producto] += 1

                df_productos = pd.DataFrame(list(conteo_productos.items()), columns=["Producto", "Cantidad"])
                fig2 = px.pie(df_productos, values="Cantidad", names="Producto",
                              title="Distribución de Productos Mencionados")
                st.plotly_chart(fig2, use_container_width=True)
        else:
            st.error("No se pudieron generar puntuaciones para los registros.")
else:
    st.error("El archivo no existe.")
