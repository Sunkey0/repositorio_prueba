# ... (código anterior)

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
        
        # Seleccionar solo las columnas necesarias de df_ia
        df_ia = df_ia[["ID", "Puntuación", "Criterios"]]
        
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
