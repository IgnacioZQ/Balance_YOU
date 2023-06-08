# Conexion SQL y SSH

from sshtunnel import SSHTunnelForwarder, SSH_TIMEOUT
import MySQLdb as db

# Interfaz

import streamlit as st
from streamlit_option_menu import option_menu
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd

# Configuraciones de la página

st.set_page_config(page_title = "Balance YOU",
                   page_icon = None,
                   layout = "centered",
                   initial_sidebar_state = "auto",
                   menu_items = None)

# Menu Principal

with st.sidebar:
    selected = option_menu(" ¡Hola Recepcion! ", ["Panel de Inicio", "Remuneraciones", "Información Contable", "Desglose de Actividades"], 
     icons=["house", "cash", "piggy-bank", "display"], menu_icon = " ", default_index = 0)
    selected

#   Conexión y Query a la Base de Datos 

def query(q):

    SSH_TIMEOUT = 1.0

    with SSHTunnelForwarder(                                                   
          ssh_address_or_host=(st.secrets['host'], 22),                          
          ssh_username=st.secrets['user'],                                      
          ssh_pkey=st.secrets['key'],                                           
          allow_agent=True,                                                      
          remote_bind_address=(st.secrets['remote'], st.secrets['port']),
          local_bind_address=('0.0.0.0', 3307)
     ) as server:

          print("Conectado")
                    
          conn = db.connect(
               host=st.secrets['local'],                           
               port=server.local_bind_port,                                         
               user=st.secrets['user'],                                              
               passwd=st.secrets['password'],                                        
               db=st.secrets['database']
               )                                            

          return pd.read_sql_query(q, conn, parse_dates=['Fecha'])

# Importar Data

df = query('''select ap.id,u.name,u.lastnames,ac.Abono,ac.Precio_Prestacion,ac.Profesional,ac.Fecha_Realizacion,a.name from yjb.action_mls ac join yjb.appointment_mls ap join yjb.users u join yjb.users_alliances_pivot uap join yjb.alliances a
on ac.Tratamiento_Nr = ap.Tratamiento_Nr and ap.Rut_Paciente = u.rut and u.id = uap.user_id and uap.alliance_id = a.id
order by ac.Tratamiento_Nr''')

# Manipulación de la Base de Datos

df.columns = ["ID", 'Nombres', 'Apellidos', 'Abono', 'Precio', 'Profesional', 'Fecha', "Convenio"]

df["Usuario"] = df.Nombres.str.cat(df.Apellidos, sep = " ")

df["Diferencia"] = df["Precio"] - df["Abono"] 

df_1= df[["Usuario", "Abono", "Precio", "Diferencia", "Profesional", "Fecha", "Convenio"]]

df_2= df[["Usuario", "Precio", "Abono", "Diferencia"]]

df_2 = df_2.groupby(by = "Usuario", as_index = False).sum()

# Organizacion de Streamlit

Usuarios = df_1["Usuario"].drop_duplicates().unique().tolist()

Convenios = df_1['Convenio'].unique().tolist()

# Filtros

Usuario_selector = st.sidebar.selectbox("Buscar: ", Usuarios)

ciudad_selector = st.multiselect("Convenio",
                                 Convenios,
                                 default = "Sin Convenio")

# DataFrames

st.dataframe(df_1.loc[(df_1['Usuario'] == Usuario_selector)])

st.dataframe(df_2.loc[(df_2['Usuario'] == Usuario_selector)])

df_1 = df.loc[(df['Usuario'] == Usuario_selector)]

# Gráficos

pie_chart = px.pie(df_1,
                   title = 'Profesionales con los que se atendió',
                   values = 'Precio',
                   names = 'Profesional')

st.plotly_chart(pie_chart)

Graph_1 = px.bar(df_1, x = "Fecha", y = "Precio", title = "Valor de atenciones por Fecha", color = "Profesional")

st.write(Graph_1)