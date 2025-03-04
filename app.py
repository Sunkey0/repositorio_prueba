import pandas as pd
import streamlit as st
import google.generativeai as genai
import clave  # Asegúrate de que este módulo contenga tu API key de Gemini
import os

# Configuración de la API Gemini
GEMINI_API_KEY = clave.key
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

# Función para procesar la respuesta de la IA
def procesar_respuesta_ia(respuesta, num_filas):
    try:
        # Dividir la respuesta en líneas
        lineas = [linea.strip() for linea in respuesta.split('\n') if linea.strip()]
        
        # Filtrar solo las líneas que tienen el formato esperado (descripción, puntuación)
        lineas_filtradas = []
        for linea in lineas:
            # Eliminar comillas dobles innecesarias
            linea = linea.replace('"', '')
            
            # Dividir la línea en campos usando comas como delimitadores
            partes = linea.split(',')
            if len(partes) >= 2:  # Verificar que haya al menos dos partes
                descripcion = partes[0].strip()
                puntuacion = partes[1].strip()
                lineas_filtradas.append([descripcion, puntuacion])
        
        # Verificar que el número de líneas coincida con el número de filas del DataFrame
        if len(lineas_filtradas) != num_filas:
            st.error(f"Error: La respuesta de la IA tiene {len(lineas_filtradas)} líneas válidas, pero se esperaban {num_filas}.")
            return None
        
        # Crear un DataFrame con las nuevas columnas
        df_nuevas_columnas = pd.DataFrame(lineas_filtradas, columns=["Descripcion_Empresa", "Calificacion_Prospecto"])
        return df_nuevas_columnas
    except Exception as e:
        st.error(f"Error al procesar la respuesta de la IA: {e}")
        return None

# Configuración de la aplicación Streamlit
st.title("Análisis de Empresas Colombianas")
st.write("Esta aplicación analiza empresas colombianas y genera una descripción y una puntuación de prospecto usando IA.")

# Cargar el archivo CSV
archivo = "empresas_colombia_2.csv"
if os.path.exists(archivo):
    df = pd.read_csv(archivo, quotechar='"', delimiter=",", encoding="utf-8-sig")
    
    # Mostrar el DataFrame original
    st.subheader("Datos Originales")
    st.write(df)
    
    # Prompt específico para el análisis
    prompt = ("A partir de los datos suministrados, agrega dos columnas: \n"
              "1. Descripción breve de la empresa con base en su nombre y actividad. \n"
              "2. Evaluación del prospecto de cliente para una empresa del sector industrial que vende repuestos industriales, bandas transportadoras, cintas, estribadores, carretillas, lubricantes, grasas grado alimenticio y otros productos relacionados con logística y transmisión de potencia. \n"
              "La evaluación debe ser una calificación del 1 al 10 donde 1 es el peor prospecto y 10 el mejor, con base en la actividad o sector de la empresa. \n"
              "Solo responde con las dos columnas en formato CSV, sin texto adicional.")
    
    # Botón para ejecutar el análisis
    if st.button("Generar Descripción y Puntuación"):
        # Llamar a la IA para obtener las dos nuevas columnas
        respuesta = call_ia_model(df, prompt)
        
        # Mostrar la respuesta de la IA
        st.subheader("Respuesta de la IA")
        st.text(respuesta)
        
        # Procesar la respuesta de la IA
        df_nuevas_columnas = procesar_respuesta_ia(respuesta, len(df))
        
        if df_nuevas_columnas is not None:
            # Unir el DataFrame original con las nuevas columnas
            df = pd.concat([df, df_nuevas_columnas], axis=1)
            
            # Mostrar el DataFrame actualizado
            st.subheader("Datos Actualizados")
            st.write(df)
            
            # Guardar el nuevo CSV con las columnas agregadas
            df.to_csv("empresas_colombia_con_ia.csv", index=False, encoding="utf-8-sig")
            st.success("Archivo generado exitosamente con las columnas agregadas.")
        else:
            st.error("No se pudieron agregar las columnas debido a un error en la respuesta de la IA.")
else:
    st.error("El archivo no existe.")
