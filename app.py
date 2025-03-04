import pandas as pd
import streamlit as st
import google.generativeai as genai
import os
import ast  # Para convertir la respuesta de la IA en una estructura de Python

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
def procesar_respuesta_ia(respuesta):
    try:
        # Convertir la respuesta de la IA en una estructura de Python
        respuesta_limpia = respuesta.strip().replace("```python", "").replace("```", "").strip()
        datos = ast.literal_eval(respuesta_limpia)  # Convertir a lista o diccionario
        
        # Verificar que la estructura sea válida
        if isinstance(datos, list) and all(isinstance(item, dict) for item in datos):
            return datos
        else:
            st.error("La respuesta de la IA no es una lista de diccionarios válida.")
            return None
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
              "[{'ID': '123', 'Nombre': 'Empresa A', 'Puntuación': 8, 'Criterios': 'Buena relevancia en el sector industrial.'}, ...]")
    
    # Botón para ejecutar el análisis
    if st.button("Generar Puntuación"):
        # Llamar a la IA para obtener las puntuaciones
        respuesta = call_ia_model(df, prompt)
        
        # Mostrar la respuesta de la IA
        st.subheader("Respuesta de la IA")
        st.text(respuesta)
        
        # Procesar la respuesta de la IA
        datos_ia = procesar_respuesta_ia(respuesta)
        
        if datos_ia:
            # Crear un DataFrame con los resultados de la IA
            df_ia = pd.DataFrame(datos_ia)
            
            # Mostrar el DataFrame generado por la IA
            st.subheader("Resultados de la IA")
            st.write(df_ia)
            
            # Fusionar los resultados con el DataFrame original
            df = df.merge(df_ia, on="ID", how="left")
            
            # Mostrar el DataFrame actualizado
            st.subheader("Datos Actualizados")
            st.write(df)
            
            # Guardar el nuevo CSV con las columnas agregadas
            df.to_csv("empresas_colombia_con_puntuacion.csv", index=False, encoding="utf-8-sig")
            st.success("Archivo generado exitosamente con las puntuaciones y criterios agregados.")
        else:
            st.error("No se pudieron agregar las puntuaciones debido a un error en la respuesta de la IA.")
else:
    st.error("El archivo no existe.")
