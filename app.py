import pandas as pd
import streamlit as st
import google.generativeai as genai
import os

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
        # Dividir la respuesta en líneas
        lineas = [linea.strip() for linea in respuesta.split('\n') if linea.strip()]
        
        # Convertir las líneas en una lista de IDs, nombres, puntuaciones y criterios
        ids = []
        nombres = []
        puntuaciones = []
        criterios = []
        lineas_no_procesadas = []  # Para almacenar líneas que no se pudieron procesar
        
        for linea in lineas:
            try:
                # Ignorar encabezados o líneas vacías
                if linea.startswith("ID,Nombre,Puntuación,Criterios de puntuación") or not linea:
                    continue
                
                # Procesar la línea como CSV
                partes = linea.split(",")
                if len(partes) == 4:
                    id_empresa = partes[0].strip()
                    nombre = partes[1].strip()
                    puntuacion = int(partes[2].strip())
                    criterio = partes[3].strip()
                    
                    if 1 <= puntuacion <= 10:  # Validar que la puntuación esté en el rango correcto
                        ids.append(id_empresa)
                        nombres.append(nombre)
                        puntuaciones.append(puntuacion)
                        criterios.append(criterio)
                    else:
                        lineas_no_procesadas.append(linea)  # Guardar línea no válida
                else:
                    lineas_no_procesadas.append(linea)  # Guardar línea no válida
            except ValueError:
                lineas_no_procesadas.append(linea)  # Guardar línea no válida
        
        # Mostrar advertencias si hay líneas no procesadas
        if lineas_no_procesadas:
            st.warning(f"Algunas líneas no pudieron procesarse: {lineas_no_procesadas}")
        
        return ids, nombres, puntuaciones, criterios
    except Exception as e:
        st.error(f"Error al procesar la respuesta de la IA: {e}")
        return None, None, None, None

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
              "Responde con el siguiente formato: \n"
              "ID,Nombre,Puntuación,Criterios de puntuación \n"
              "Asegúrate de generar una puntuación para cada empresa en el archivo CSV.")
    
    # Botón para ejecutar el análisis
    if st.button("Generar Puntuación"):
        # Llamar a la IA para obtener las puntuaciones
        respuesta = call_ia_model(df, prompt)
        
        # Mostrar la respuesta de la IA
        st.subheader("Respuesta de la IA")
        st.text(respuesta)
        
        # Procesar la respuesta de la IA
        ids, nombres, puntuaciones, criterios = procesar_respuesta_ia(respuesta)
        
        # Crear un nuevo DataFrame con los resultados de la IA
        df_ia = pd.DataFrame({
            "ID": ids if ids else [],
            "Nombre": nombres if nombres else [],
            "Puntuacion_Prospecto": puntuaciones if puntuaciones else [],
            "Criterios_Puntuacion": criterios if criterios else []
        })
        
        # Mostrar el DataFrame generado por la IA
        st.subheader("Resultados de la IA")
        st.write(df_ia)
        
        if ids and nombres and puntuaciones and criterios:
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
