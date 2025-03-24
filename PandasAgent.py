# NOME:
# TURMA:
# laurindo.dumba@univille.br

# Importação das bibliotecas, para criar interfaces,
# realizar a manipulação dos dados e acesso ao modelo e geração de gráficos
import streamlit as st
import pandas as pd
import numpy as np
import os
from groq import Groq
import plotly.express as px

st.title("Univille AI") #Criação do titulo

#
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")

if not GROQ_API_KEY:
    st.error("A chave GROQ_API_KEY não foi definida corretamente!")
    st.stop()  
client = Groq(api_key=GROQ_API_KEY)

uploaded_files = st.file_uploader(
    "Escolha o seu arquivo CSV", accept_multiple_files=True, type=["csv"]
)


dataframes = {}

if uploaded_files:
    for uploaded_file in uploaded_files:
        df = pd.read_csv(uploaded_file)
        dataframes[uploaded_file.name] = df
        st.write(f"**{uploaded_file.name}**") 
        st.dataframe(df.head())
    
    
user_query = st.text_area("Conversa com os teus dados")


if st.button("Enviar Pergunta") and user_query:
    prompt = f"Responda como um analista de dados. Pergunta: {user_query}"
    response = client.chat.completions.create(model="llama3-8b-8192",
                                              messages=[{"role": "user", "content": prompt}])
    st.write("### Resposta do Agente:")
    st.write(response.choices[0].message.content)
    
    st.write("Resposta do Agente:")
    st.write(response.choices[0].message.content)
    
graph_request = st.text_input("Qual é a coluna que deseja ver o gráfico:")
selected_file = st.selectbox("Escolha um arquivo para visualizar:", list(dataframes.keys())) if dataframes else None

if st.button("Gerar Gráfico") and graph_request and selected_file:
    df = dataframes[selected_file]
    if graph_request in df.columns:
        fig = px.histogram(df, x=graph_request, title=f"Distribuição de {graph_request}")
        st.plotly_chart(fig)
    else:
        st.warning("Coluna não encontrada no dataset!")