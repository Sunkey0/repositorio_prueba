import pandas as pd
import streamlit as st
import google.generativeai as genai
import clave  # Asegúrate de que este módulo contenga tu API key de Gemini
import os
import streamlit as st
import pandas as pd
import google.generativeai as genai

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

# Función para procesar la respuesta de la IA
def procesar_respuesta_ia(respuesta, num_filas):
    try:
        # Dividir la respuesta en líneas
        lineas = [linea.strip() for linea in respuesta.split('\n') if linea.strip()]
        
        # Verificar que el número de líneas coincida con el número de filas del DataFrame
        if len(lineas) != num_filas:
            st.error(f"Error: La respuesta de la IA tiene {len(lineas)} líneas, pero se esperaban {num_filas}.")
            return None
        
        # Convertir las líneas en una lista de puntuaciones
        puntuaciones = []
        for linea in lineas:
            try:
                puntuacion = int(linea.strip())
                if 1 <= puntuacion <= 10:  # Validar que la puntuación esté en el rango correcto
                    puntuaciones.append(puntuacion)
                else:
                    st.error(f"Error: La puntuación '{puntuacion}' no está en el rango de 1 a 10.")
                    return None
            except ValueError:
                st.error(f"Error: La línea '{linea}' no es un número válido.")
                return None
        
        return puntuaciones
    except Exception as e:
        st.error(f"Error al procesar la respuesta de la IA: {e}")
        return None

# Configuración de la aplicación Streamlit
st.title("Análisis de Empresas Colombianas")
st.write("Esta aplicación analiza empresas colombianas y genera una puntuación de prospecto usando IA.")

# Cargar el archivo CSV
archivo = "empresas_colombia_2.csv"
if os.path.exists(archivo):
    df = pd.read_csv(archivo, quotechar='"', delimiter=",", encoding="utf-8-sig")
    
    # Mostrar el DataFrame original
    st.subheader("Datos Originales")
    st.write(df)
    
    # Prompt específico para el análisis
    prompt = ("Eres un analista de negocios especializado en el sector industrial. Tu tarea es evaluar el potencial de cada empresa como cliente para una compañía que vende repuestos industriales, bandas transportadoras, cintas, estribadores, carretillas, lubricantes, grasas grado alimenticio y otros productos relacionados con logística y transmisión de potencia. \n"
              "Para cada empresa, asigna una puntuación del 1 al 10, donde 1 es el peor prospecto y 10 el mejor. Considera los siguientes factores: \n"
              "- Categoría de la empresa. \n"
              "- Actividad principal. \n"
              "- Ubicación (ciudad y departamento). \n"
              "- Relevancia para el sector industrial. \n"
              "Solo responde con un número por empresa, sin texto adicional.")
    
    # Botón para ejecutar el análisis
    if st.button("Generar Puntuación"):
        # Llamar a la IA para obtener las puntuaciones
        respuesta = call_ia_model(df, prompt)
        
        # Mostrar la respuesta de la IA
        st.subheader("Respuesta de la IA")
        st.text(respuesta)
        
        # Procesar la respuesta de la IA
        puntuaciones = procesar_respuesta_ia(respuesta, len(df))
        
        if puntuaciones is not None:
            # Agregar las puntuaciones al DataFrame
            df["Puntuacion_Prospecto"] = puntuaciones
            
            # Mostrar el DataFrame actualizado
            st.subheader("Datos Actualizados")
            st.write(df)
            
            # Guardar el nuevo CSV con las columnas agregadas
            df.to_csv("empresas_colombia_con_puntuacion.csv", index=False, encoding="utf-8-sig")
            st.success("Archivo generado exitosamente con las puntuaciones agregadas.")
        else:
            st.error("No se pudieron agregar las puntuaciones debido a un error en la respuesta de la IA.")
else:
    st.error("El archivo no existe.")
