

import streamlit as st
import pandas as pd
import os
import sqlite3
from groq import Groq
from pypdf import PdfReader


import plotly.express as px

# --- CONFIGURAÇÃO DE CAMINHOS DINÂMICOS 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# --- INTERFACE
col1, col2 = st.columns([1, 5])
with col1:
    st.image(os.path.join(ASSETS_DIR, "Depeto.png"), width=80)
with col2:
    st.title("DEPÊTO")

cls1, cls2, cls3 = st.columns(3)
for c, texto in zip(
    [cls1, cls2, cls3],
    ["Escreva alguma descrição", "Faça uma pergunta chave", "Crie outra pergunta"]
):
    with c:
        st.markdown(
            f"""
            <div style="background-color:#f0f0f0; padding:10px; border-radius:50px; color: black">
                <strong>{texto}</strong>
            </div>
            """,
            unsafe_allow_html=True
        )

# --- CONFIGURAÇÃO 
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "chave")
if not GROQ_API_KEY:
    st.error("A chave GROQ_API_KEY não foi definida corretamente!")
    st.stop()
client = Groq(api_key=GROQ_API_KEY)

# --- BANCO DE DADOS
DB_PATH = os.path.join(BASE_DIR, "arquivos.db")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS arquivos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        conteudo TEXT
    )
""")
conn.commit()

# --- SIDEBAR PARA UPLOAD DE ARQUIVOS
with st.sidebar:
    st.image(os.path.join(ASSETS_DIR, "logo.png"))
    uploaded_files = st.file_uploader(
        "Escolha seus arquivos PDF", 
        accept_multiple_files=True, 
        type=["pdf"]
    )

# --- Processar arquivos
if uploaded_files:
    for uploaded_file in uploaded_files:
        pdf_reader = PdfReader(uploaded_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
        # Salva no banco
        cursor.execute("INSERT INTO arquivos (nome, conteudo) VALUES (?, ?)", 
                       (uploaded_file.name, text))
        conn.commit()
        st.success(f"Arquivo '{uploaded_file.name}' salvo no banco de dados!")

# --- Validador
cursor.execute("SELECT COUNT(*) FROM arquivos")
num_files = cursor.fetchone()[0]

user_query = st.text_area("Digite sua pergunta:")

if st.button("Enviar Pergunta"):
    if num_files == 0:
        st.warning("Por favor, envie ao menos um arquivo PDF antes de fazer perguntas.")
    elif not user_query.strip():
        st.warning("Digite uma pergunta antes de enviar.")
    else:
        # Recupera todo o conteúdo do banco para o contexto
        cursor.execute("SELECT nome, conteudo FROM arquivos")
        all_files = cursor.fetchall()
        context = "\n\n".join([f"Arquivo: {n}\nConteúdo: {c[:3000]}" for n, c in all_files])  # limita texto
        prompt = f"Você é um analista de dados. Use as informações abaixo para responder:\n\n{context}\n\nPergunta: {user_query}"

        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}]
        )
        st.write("### Resposta do Agente:")
        st.write(response.choices[0].message.content)

# Fecha a conexão
conn.close()
