import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse

# Configuração da Página
st.set_page_config(page_title="FARMA LAGOS - PDV", page_icon="💊", layout="centered")

st.markdown("<h1 style='text-align: center;'>💊 FARMA LAGOS</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>CNPJ: 68.530.976/0001-00</p>", unsafe_allow_html=True)

# Função para Horário de Brasília
def get_brasilia_time():
    return datetime.utcnow() - timedelta(hours=3)

@st.cache_data
def carregar_dados():
    try:
        df = pd.read_csv("estoque_drogaria.csv")
        df.columns = df.columns.str.strip()
        df = df.rename(columns={"Descrição": "Produto", "Quantidade": "Estoque", "Preço": "Preco"})
        return df
    except:
        return pd.DataFrame(columns=["Produto", "Preco", "Estoque"])

df = carregar_dados()

if 'carrinho' not in st.session_state:
    st.session_state.carrinho = []

# Menu Lateral
menu = st.sidebar.radio("Navegação:", ["PDV & Vendas", "Estoque"])

if menu == "PDV & Vendas":
    st.subheader("🛒 Carrinho de Compras")
    
    # Busca e Adição
    pesquisa = st.text_input("🔍 Buscar produto:")
    if pesquisa:
        df_f = df[df["Produto"].astype(str).str.contains(pesquisa, case=False, na=False)]
        if not df_f.empty:
            prod = st.selectbox("Selecione:", df_f["Produto"].tolist())
            d = df_f[df_f["Produto"] == prod].iloc[0]
            preco = st.number_input("Preço Un.:", value=float(d["Preco"]), format="%.2f")
            qtd = st.number_input("Qtd:", min_value=1, value=1)
            if st.button("➕ Adicionar"):
                st.session_state.carrinho.append({"Produto": prod, "Preco": preco, "Qtd": qtd})
                st.rerun()

    # Exibição do Carrinho
    if st.session_state.carrinho:
        total_produtos = 0
        lista_itens = ""
        for i, item in enumerate(st.session_state.carrinho):
            sub = item['Preco'] * item['Qtd']
            total_produtos += sub
            lista_itens += f"{i+1:02d} | {item['Qtd']}x {item['Produto']} | R$ {item['Preco']:.2f} -> Sub: R$ {sub:.2f}\n"

        # Entrega
        usar_entrega = st.checkbox("🚚 Adicionar entrega?")
        taxa = 0.0
        endereco = ""
        if usar_entrega:
            endereco = st.text_input("Endereço do Cliente:")
            taxa = st.number_input("Valor da Taxa (R$):", value=5.00)
        
        total_final = total_produtos + taxa
        
        st.write("---")
        cliente = st.text_input("Nome do Cliente:")
        whatsapp = st.text_input("WhatsApp (apenas números com DDD):")
        
        if st.button("✅ GERAR CUPOM E ENVIAR WHATSAPP"):
            msg = f"=\nFARMA LAGOS - CUPOM FISCAL\nCNPJ: 68.530.976/0001-00\nEndereço: Armação dos Búzios - RJ\n=========================\nDATA: {get_brasilia_time().strftime('%d/%m/%Y %H:%M:%S')}\n-------------------------\nCLIENTE: {cliente}\n-------------------------\nCOD | QTD | DESCRIÇÃO | UNIT | TOTAL\n{lista_itens}-------------------------\n"
            if usar_entrega:
                msg += f"ENTREGA: {endereco}\nTAXA DE ENTREGA: R$ {taxa:.2f}\n-------------------------\n"
            msg += f"TOTAL GERAL: R$ {total_final:.2f}\n=========================\nObrigado pela preferência!\nSua saúde em primeiro lugar."
            
            link = f"https://wa.me/55{whatsapp}?text={urllib.parse.quote(msg)}"
            st.markdown(f"[🔗 CLIQUE AQUI PARA ENVIAR O CUPOM NO WHATSAPP]({link})")
            st.text_area("Pré-visualização do Cupom:", msg, height=300)

else:
    st.dataframe(df)
