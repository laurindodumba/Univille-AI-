import streamlit as st
import pandas as pd
import os
import sqlite3
from pypdf import PdfReader
from openai import OpenAI
from dotenv import load_dotenv
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

# --- CONFIGURAR OPENAI CLIENT
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

# --- Processar arquivos e salvar no banco
if uploaded_files:
    for uploaded_file in uploaded_files:
        pdf_reader = PdfReader(uploaded_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
        cursor.execute("INSERT INTO arquivos (nome, conteudo) VALUES (?, ?)", 
                       (uploaded_file.name, text))
        conn.commit()
        st.success(f"Arquivo '{uploaded_file.name}' salvo no banco de dados!")

# --- Carregar conteúdo dos PDFs para contexto
cursor.execute("SELECT nome, conteudo FROM arquivos")
all_files = cursor.fetchall()
context = "\n\n".join([f"Arquivo: {n}\nConteúdo: {c[:3000]}" for n, c in all_files]) if all_files else ""

# --- Inicializar histórico de mensagens
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "Você é um analista de dados que responde com base nos PDFs carregados."}
    ]

# --- Mostrar histórico do chat
st.write("### 💬 Chat:")
for msg in st.session_state.messages[1:]:
    if msg["role"] == "user":
        st.markdown(f"🧑‍💻 **Você:** {msg['content']}")
    else:
        st.markdown(f"🤖 **Agente:** {msg['content']}")

# --- Caixa de entrada
user_query = st.chat_input("Digite sua pergunta sobre os PDFs...")

# --- Quando o usuário envia uma nova pergunta
if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})

    # Adiciona contexto dos PDFs
    prompt = f"Use as informações dos arquivos abaixo para responder:\n\n{context}\n\nPergunta: {user_query}"

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=st.session_state.messages + [{"role": "user", "content": prompt}]
    )

    answer = response.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": answer})

    # Atualiza a interface
    st.rerun()

# Fecha conexão
conn.close()
