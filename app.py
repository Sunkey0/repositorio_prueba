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

# Función para llamar a la IA
def call_ia_model(data, prompt, model_name="gemini-1.5-flash"):
    try:
        if isinstance(data, pd.DataFrame):
            data_str = data.to_csv(index=False)
        else:
            data_str = str(data)

        full_prompt = f"{prompt}\n\nDatos:\n{data_str}"
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(full_prompt)

        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

# Función para extraer la lista de diccionarios de la respuesta de la IA
def extraer_lista_desde_respuesta(respuesta):
    try:
        # Usar una expresión regular para encontrar la lista de diccionarios
        match = re.search(r"\[.*\]", respuesta, re.DOTALL)
        if match:
            lista_str = match.group(0)  # Extraer la lista como cadena
            return lista_str
        else:
            st.error("No se encontró una lista de diccionarios en la respuesta de la IA.")
            return None
    except Exception as e:
        st.error(f"Error al extraer la lista de diccionarios: {e}")
        return None

# Función para procesar la respuesta de la IA
def procesar_respuesta_ia(respuesta):
    try:
        # Extraer la lista de diccionarios de la respuesta
        lista_str = extraer_lista_desde_respuesta(respuesta)
        if not lista_str:
            return None
        
        # Convertir la cadena en una lista de diccionarios
        datos = ast.literal_eval(lista_str)
        
        # Verificar que la estructura sea válida
        if isinstance(datos, list) and all(isinstance(item, dict) for item in datos):
            return datos
        else:
            st.error("La respuesta de la IA no es una lista de diccionarios válida.")
            return None
    except Exception as e:
        st.error(f"Error al procesar la respuesta de la IA: {e}")
        return None

# Función para generar un informe ejecutivo en Markdown
def generar_informe(df):
    # Calcular métricas clave
    total_empresas = len(df)
    alto_potencial = df[df["Puntuación_y"] >= 7]
    medio_potencial = df[(df["Puntuación_y"] >= 5) & (df["Puntuación_y"] < 7)]
    bajo_potencial = df[df["Puntuación_y"] < 5]
    
    porcentaje_alto_potencial = (len(alto_potencial) / total_empresas) * 100
    puntuacion_promedio = df["Puntuación_y"].mean()
    
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
    for sector, grupo in df.groupby("Categoría"):
        informe_md += (
            f"- **{sector}**: {len(grupo)} empresas, Puntuación promedio: {grupo['Puntuación_y'].mean():.2f}\n"
        )
    
    return informe_md

# Título de la aplicación
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
        "Eres un analista de negocios especializado en el sector industrial. Tu tarea es evaluar el potencial de cada empresa como cliente para una compañía que vende repuestos industriales, bandas transportadoras, cintas, estribadores, carretillas, lubricantes, grasas grado alimenticio y otros productos relacionados con logística y transmisión de potencia. \n"
        "Anteriormente, la empresa ha vendido a empresas como Colanta, productoras de café, productoras de productos alimenticios, canteras, productoras de pinturas, entre otros. La idea es llegar a empresas grandes que puedan generar tickets considerables. \n"
        "Para cada empresa, asigna una puntuación del 1 al 10, donde 1 es el peor prospecto y 10 el mejor. Considera los siguientes factores: \n"
        "- Categoría de la empresa. \n"
        "- Actividad principal. \n"
        "- Productos que se pueden ofrecer. \n"
        "- Relevancia para el sector industrial. \n"
        "Responde con una lista de diccionarios en formato Python, donde cada diccionario tenga las siguientes claves: \n"
        "- 'ID': El ID de la empresa. \n"
        "- 'Nombre': El nombre de la empresa. \n"
        "- 'Puntuación': La puntuación asignada (1-10). \n"
        "- 'Criterios': Los criterios de puntuación. \n"
        "Ejemplo de formato: \n"
        "[{'ID': '123', 'Nombre': 'Empresa A', 'Puntuación': 8, 'Criterios': 'Buena relevancia en el sector industrial.'}, ...]"
    )
    
    # Botón para ejecutar el análisis
    if st.button("Generar Puntuación"):
        # Llamar a la IA para obtener las puntuaciones
        respuesta = call_ia_model(df, prompt)
        
        # Mostrar la respuesta de la IA
        with st.expander("Ver Respuesta de la IA"):
            st.text(respuesta)
        
        # Procesar la respuesta de la IA
        datos_ia = procesar_respuesta_ia(respuesta)
        
        if datos_ia:
            # Crear un DataFrame con los resultados de la IA
            df_ia = pd.DataFrame(datos_ia)
            
            # Mostrar el DataFrame generado por la IA en un menú expandible
            with st.expander("Ver Resultados de la IA"):
                st.dataframe(df_ia)
            
            # Seleccionar solo las columnas necesarias de df_ia
            df_ia = df_ia[["ID", "Puntuación", "Criterios"]]
            
            # Fusionar los resultados con el DataFrame original
            df = df.merge(df_ia, on="ID", how="left")
            
            # Mostrar el DataFrame actualizado en un menú expandible
            with st.expander("Ver Datos Actualizados"):
                st.dataframe(df)
            
            # Generar el informe ejecutivo en Markdown
            informe_md = generar_informe(df)
            
            # Mostrar el informe en forma de KPIs
            st.markdown("## KPIs del Informe")
            
            # Crear columnas para los KPIs
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total de Empresas", len(df))
            
            with col2:
                st.metric("Empresas de Alto Potencial", len(df[df["Puntuación_y"] >= 7]))
            
            with col3:
                st.metric("Puntuación Promedio", f"{df['Puntuación_y'].mean():.2f}")
            
            # Crear pestañas para organizar el contenido
            tab1, tab2 = st.tabs(["Informe", "Gráficas"])
            
            with tab1:
                # Contenido de la pestaña "Informe"
                st.markdown("## Informe ")
                st.markdown(informe_md)
            
            with tab2:
                # Contenido de la pestaña "Gráficas"
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

            # Definimos la lista de productos que buscamos en la columna 'Criterios'
            lista_productos = [
                "Bandas transportadoras",
                "Carretillas",
                "Lubricantes",
                "Cintas",
                "Estribadores"
            ]

            # Filtramos las empresas de medio y alto potencial (Puntuación >= 5)
            df_filtrado = df[df["Puntuación_y"] >= 5]

            # Contamos las menciones de cada producto dentro de 'Criterios'
            conteo_productos = {producto: 0 for producto in lista_productos}

            for _, fila in df_filtrado.iterrows():
                criterios_lower = str(fila["Criterios"]).lower()  # Convertimos a minúsculas para búsqueda
                for producto in lista_productos:
                    # Si el producto aparece en el texto de 'Criterios', incrementamos el contador
                    if producto.lower() in criterios_lower:
                        conteo_productos[producto] += 1

            # Convertimos el conteo en un DataFrame
            df_productos = pd.DataFrame(list(conteo_productos.items()), columns=["Producto", "Cantidad"])

            # Generamos la gráfica (pie chart) con Plotly
            fig2 = px.pie(
                df_productos,
                values="Cantidad",
                names="Producto",
                title="Distribución de Productos Mencionados"
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.error("No se pudieron agregar las puntuaciones debido a un error en la respuesta de la IA.")
else:
    st.error("El archivo no existe.")
