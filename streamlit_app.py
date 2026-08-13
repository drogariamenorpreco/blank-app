import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse

# Configuração da Página
st.set_page_config(page_title="FARMA LAGOS", page_icon="💊", layout="centered")

# Cabeçalho Limpo
st.markdown("<h1 style='text-align: center;'>💊 FARMA LAGOS</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>CNPJ: 68.530.976/0001-00</p>", unsafe_allow_html=True)

# Função para Horário de Brasília
def get_brasilia_time():
    return datetime.utcnow() - timedelta(hours=3)

# Carregamento do Estoque com tratamento de colunas
@st.cache_data
def carregar_dados():
    try:
        df = pd.read_csv("estoque_drogaria.csv")
        # Remove espaços extras dos nomes das colunas e padroniza
        df.columns = df.columns.str.strip()
        # Mapeia para o que o sistema espera
        rename_dict = {
            "Descrição": "Produto", 
            "Quantidade": "Estoque", 
            "Preço": "Preco"
        }
        df = df.rename(columns=rename_dict)
        # Se "Preco" não existir, tenta encontrar pela posição (índice 2)
        if "Preco" not in df.columns:
            df = df.rename(columns={df.columns[2]: "Preco"})
        return df
    except Exception as e:
        return pd.DataFrame(columns=["Produto", "Preco", "Estoque"])

df = carregar_dados()

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
            
            # Garante que o valor inicial seja número válido
            preco_val = float(dados["Preco"]) if pd.notnull(dados["Preco"]) else 0.0
            
            preco_editavel = st.number_input("Preço de Venda (R$):", value=preco_val, format="%.2f")
            qtd = st.number_input("Quantidade:", min_value=1, value=1)
            
            if st.button("➕ Adicionar ao Carrinho"):
                st.session_state.carrinho.append({"Produto": prod_sel, "Preco": preco_editavel, "Qtd": qtd})
                st.success(f"{prod_sel} adicionado!")

    if st.session_state.carrinho:
        st.write("### Carrinho")
        total = 0
        for i, item in enumerate(st.session_state.carrinho):
            st.write(f"{item['Qtd']}x {item['Produto']} - R$ {item['Preco']:.2f}")
            total += item['Preco'] * item['Qtd']
        st.write(f"**TOTAL: R$ {total:.2f}**")
        
        celular = st.text_input("WhatsApp do Cliente (apenas números):")
        if st.button("✅ Finalizar via WhatsApp"):
            msg = f"FARMA LAGOS - Resumo da compra:\nTotal: R$ {total:.2f}\nData: {get_brasilia_time().strftime('%d/%m/%Y %H:%M')}"
            link = f"https://wa.me/55{celular}?text={urllib.parse.quote(msg)}"
            st.markdown(f"[🔗 ENVIAR COMPROVANTE]({link})")

elif menu == "Entrega":
    st.subheader("🚚 Gestão de Entrega")
    end = st.text_input("Endereço:")
    if st.button("Registrar Entrega"):
        st.success(f"Entrega agendada para: {end}")

else:
    st.dataframe(df)
