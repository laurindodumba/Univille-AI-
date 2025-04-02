import streamlit as st
import fitz  # PyMuPDF
from groq import Groq  # Certifique-se de instalar a biblioteca correta

# Configurar chave da Groq
GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)

# Função para extrair texto dos PDFs
def extract_text_from_pdfs(uploaded_pdfs):
    text = ""
    for pdf in uploaded_pdfs:
        with fitz.open(stream=pdf.read(), filetype="pdf") as doc:  # Aqui pode estar o problema
            for page in doc:
                text += page.get_text("text")  # Usar "text" para texto mais limpo
    return text


def chat_with_groq(prompt, context):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "Você é um assistente que responde com base em documentos fornecidos."},
            {"role": "user", "content": f"{context}\n\nPergunta: {prompt}"}
        ]
    )
    return response.choices[0].message.content  # Acessando o conteúdo corretamente


# Interface Streamlit
def main():
    st.title("Chat com seus PDFs usando Groq")
    
    with st.sidebar:
        st.header("Upload de arquivos PDF")
        uploaded_pdfs = st.file_uploader("Adicione arquivos PDF", type="pdf", accept_multiple_files=True)

    if uploaded_pdfs:
        text = extract_text_from_pdfs(uploaded_pdfs)
        st.session_state["document_text"] = text  # Salvar o contexto do documento

    user_input = st.text_input("Digite sua pergunta:")
    
    if user_input and "document_text" in st.session_state:
        response = chat_with_groq(user_input, st.session_state["document_text"])
        st.write("Resposta:", response)

if __name__ == "__main__":
    main()
