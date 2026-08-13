import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse

# Configuração da Página
st.set_page_config(page_title="FARMA BÚZIOS - PDV", page_icon="💊", layout="centered")

st.markdown("<h1 style='text-align: center;'>💊 FARMA BÚZIOS</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>CNPJ: 68.530.976/0001-00</p>", unsafe_allow_html=True)

def get_brasilia_time():
    return datetime.utcnow() - timedelta(hours=3)

@st.cache_data
def carregar_dados():
    try:
        df = pd.read_csv("estoque_drogaria.csv")
        # Limpa espaços e nomes das colunas para evitar o erro
        df.columns = df.columns.str.strip()
        
        # Mapeamento flexível das colunas do seu CSV
        mapeamento = {
            "Descrição": "Produto",
            "Quantidade": "Estoque",
            "Preço": "Preco",
            "Preco": "Preco" # Caso já esteja sem acento
        }
        df = df.rename(columns=mapeamento)
        
        # Garantia final: pega a 3ª coluna se "Preco" não for encontrada
        if "Preco" not in df.columns:
            df = df.rename(columns={df.columns[2]: "Preco"})
            
        return df
    except Exception as e:
        st.error(f"Erro ao ler arquivo: {e}")
        return pd.DataFrame()

df = carregar_dados()

if 'carrinho' not in st.session_state:
    st.session_state.carrinho = []

menu = st.sidebar.radio("Navegação:", ["PDV & Vendas", "Estoque"])

if menu == "PDV & Vendas":
    st.subheader("🛒 Carrinho")
    
    pesquisa = st.text_input("🔍 Buscar produto:")
    if pesquisa:
        df_f = df[df["Produto"].astype(str).str.contains(pesquisa, case=False, na=False)]
        if not df_f.empty:
            prod = st.selectbox("Selecione:", df_f["Produto"].tolist())
            dados = df_f[df_f["Produto"] == prod].iloc[0]
            
            # Garantia de valor numérico
            preco_default = float(dados["Preco"]) if pd.notnull(dados["Preco"]) else 0.0
            
            preco_edit = st.number_input("Preço Unitário (R$):", value=preco_default, format="%.2f")
            qtd = st.number_input("Quantidade:", min_value=1, value=1)
            
            if st.button("➕ Adicionar ao Carrinho"):
                st.session_state.carrinho.append({"Produto": prod, "Preco": preco_edit, "Qtd": qtd})
                st.rerun()

    if st.session_state.carrinho:
        total_produtos = 0
        lista_itens = ""
        for i, item in enumerate(st.session_state.carrinho):
            sub = item['Preco'] * item['Qtd']
            total_produtos += sub
            lista_itens += f"{i+1:02d} | {item['Qtd']}x {item['Produto']} | R$ {item['Preco']:.2f} | Sub: R$ {sub:.2f}\n"

        st.write("---")
        usar_entrega = st.checkbox("🚚 Adicionar entrega?")
        taxa = 0.0
        endereco = ""
        if usar_entrega:
            endereco = st.text_input("Endereço do Cliente:")
            taxa = st.number_input("Valor da Taxa de Entrega (R$):", value=5.00)
        
        total_final = total_produtos + taxa
        cliente = st.text_input("Nome do Cliente:")
        whatsapp = st.text_input("WhatsApp (ex: 22999999999):")
        
        if st.button("✅ GERAR NOTA E ENVIAR WHATSAPP"):
            msg = f"FARMA BÚZIOS\nCNPJ: 68.530.976/0001-00\n----------------------------\nDATA: {get_brasilia_time().strftime('%d/%m/%Y %H:%M')}\nCLIENTE: {cliente}\n----------------------------\nCOD | QTD | DESC | UNIT | TOTAL\n{lista_itens}----------------------------\n"
            if usar_entrega:
                msg += f"ENTREGA: {endereco}\nTAXA: R$ {taxa:.2f}\n----------------------------\n"
            msg += f"TOTAL A PAGAR: R$ {total_final:.2f}\n============================\nObrigado pela preferência!"
            
            link = f"https://wa.me/55{whatsapp}?text={urllib.parse.quote(msg)}"
            st.markdown(f"[🔗 CLIQUE AQUI PARA ENVIAR A NOTA NO WHATSAPP]({link})")
            st.code(msg)

else:
    st.dataframe(df)
