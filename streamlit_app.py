import streamlit as st
import pandas as pd
from datetime import datetime

# Configuração da Página
st.set_page_config(page_title="Farma Lagos - Gestão e Vendas", page_icon="💊", layout="centered")

st.markdown("<h1 style='text-align: center;'>💊 FARMA LAGOS</h1>", unsafe_allow_html=True)

# Carregamento do estoque real
@st.cache_data
def carregar_dados():
    try:
        # Lê o arquivo usando as colunas que aparecem na sua imagem
        df = pd.read_csv("estoque_drogaria.csv")
        # Renomeia para o padrão que o sistema entende internamente
        df = df.rename(columns={
            "Descrição": "Produto", 
            "Quantidade": "Estoque", 
            "Preço": "Preco"
        })
        # Caso a terceira coluna tenha outro nome, ajustamos aqui
        if "Preco" not in df.columns:
            df = df.rename(columns={df.columns[2]: "Preco"})
        return df
    except Exception as e:
        st.error(f"Erro ao ler arquivo: {e}")
        return pd.DataFrame()

df = carregar_dados()

# Menu Lateral
menu = st.sidebar.radio("Ir para:", ["Emitir Pedido / NF", "Estoque & Preços"])

if menu == "Emitir Pedido / NF":
    st.subheader("🛒 Emitir Venda e Nota Fiscal")
    
    produto_pesquisa = st.text_input("🔍 Digite o nome do produto para buscar:")
    
    if produto_pesquisa:
        df_filtrado = df[df["Produto"].astype(str).str.contains(produto_pesquisa, case=False, na=False)]
        
        if not df_filtrado.empty:
            produto_selecionado = st.selectbox("Selecione o produto:", df_filtrado["Produto"].tolist())
            
            dados_prod = df_filtrado[df_filtrado["Produto"] == produto_selecionado].iloc[0]
            preco_cadastrado = float(dados_prod["Preco"])
            estoque_atual = int(dados_prod["Estoque"])
            
            st.info(f"💡 Preço: R$ {preco_cadastrado:.2f} | Estoque: {estoque_atual} un")
            
            qtd = st.number_input("Quantidade:", min_value=1, max_value=max(1, estoque_atual), value=1)
            total_item = qtd * preco_cadastrado
            
            if st.button("Gerar Nota Fiscal"):
                st.success("Nota Gerada!")
                st.markdown(f"""
                <div style="border: 2px dashed #000; padding: 15px; font-family: monospace;">
                    <b>68.530.976 CLAUDINEI DE JESUS DA SILVA JUNIOR</b><br>
                    CNPJ: 68.530.976/0001-00<br>
                    --------------------------------------------------<br>
                    <b>ITEM:</b> {produto_selecionado}<br>
                    <b>QTD:</b> {qtd} | <b>TOTAL:</b> R$ {total_item:.2f}<br>
                    --------------------------------------------------<br>
                    <b>Data:</b> {datetime.now().strftime("%d/%m/%Y %H:%M")}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("Produto não encontrado.")

elif menu == "Estoque & Preços":
    st.subheader("📦 Estoque Atual")
    st.dataframe(df)
