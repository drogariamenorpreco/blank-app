import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse

# Configuração da Página
st.set_page_config(page_title="FARMA LAGOS - PDV", page_icon="💊", layout="centered")

# Cabeçalho com seu Nome
st.markdown("<h1 style='text-align: center;'>💊 FARMA LAGOS</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center;'>Claudinei de Jesus da Silva Junior</h3>", unsafe_allow_html=True)

# Função para Horário de Brasília (UTC-3)
def get_brasilia_time():
    return datetime.utcnow() - timedelta(hours=3)

# Carregamento do Estoque
@st.cache_data
def carregar_dados():
    try:
        df = pd.read_csv("estoque_drogaria.csv")
        df = df.rename(columns={"Descrição": "Produto", "Quantidade": "Estoque", "Preço": "Preco"})
        return df
    except:
        return pd.DataFrame(columns=["Produto", "Preco", "Estoque"])

df = carregar_dados()

# Inicializa o Carrinho na sessão
if 'carrinho' not in st.session_state:
    st.session_state.carrinho = []

menu = st.sidebar.radio("Navegação:", ["Venda (PDV)", "Entrega", "Estoque"])

if menu == "Venda (PDV)":
    st.subheader("🛒 Adicionar ao Carrinho")
    produto_pesquisa = st.text_input("🔍 Buscar produto:")
    
    if produto_pesquisa:
        df_filtrado = df[df["Produto"].astype(str).str.contains(produto_pesquisa, case=False, na=False)]
        if not df_filtrado.empty:
            prod_sel = st.selectbox("Selecione:", df_filtrado["Produto"].tolist())
            dados = df_filtrado[df_filtrado["Produto"] == prod_sel].iloc[0]
            
            # Edição de preço e quantidade
            preco_editavel = st.number_input("Preço de Venda (R$):", value=float(dados["Preco"]))
            qtd = st.number_input("Quantidade:", min_value=1, value=1)
            
            if st.button("➕ Adicionar ao Carrinho"):
                st.session_state.carrinho.append({"Produto": prod_sel, "Preco": preco_editavel, "Qtd": qtd})
                st.success(f"{prod_sel} adicionado!")

    # Exibir Carrinho
    if st.session_state.carrinho:
        st.write("### Carrinho Atual")
        total = 0
        for i, item in enumerate(st.session_state.carrinho):
            st.write(f"{item['Qtd']}x {item['Produto']} - R$ {item['Preco']:.2f}")
            total += item['Preco'] * item['Qtd']
        st.write(f"**TOTAL: R$ {total:.2f}**")
        
        celular = st.text_input("WhatsApp do Cliente (apenas números com DDD):")
        if st.button("✅ Finalizar e Enviar via WhatsApp"):
            msg = f"Olá! Segue sua compra na FARMA LAGOS:\nTotal: R$ {total:.2f}\nData: {get_brasilia_time().strftime('%d/%m/%Y %H:%M')}"
            link = f"https://wa.me/55{celular}?text={urllib.parse.quote(msg)}"
            st.markdown(f"[🔗 Clique aqui para abrir o WhatsApp do cliente]({link})")

elif menu == "Entrega":
    st.subheader("🚚 Gestão de Entrega")
    end = st.text_input("Endereço do Cliente:")
    taxa = st.number_input("Taxa de Entrega (R$):", value=5.00)
    if st.button("Registrar Entrega"):
        st.success(f"Entrega agendada para: {end} | Taxa: R$ {taxa:.2f}")

else:
    st.dataframe(df)
