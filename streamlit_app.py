import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse
from fpdf import FPDF
import tempfile
import os

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
        df.columns = df.columns.str.strip()
        df = df.rename(columns={"Descrição": "Produto", "Quantidade": "Estoque", "Preço": "Preco"})
        if "Preco" not in df.columns:
            df = df.rename(columns={df.columns[2]: "Preco"})
        return df
    except:
        return pd.DataFrame(columns=["Produto", "Preco", "Estoque"])

df = carregar_dados()

if 'carrinho' not in st.session_state:
    st.session_state.carrinho = []

menu = st.sidebar.radio("Navegação:", ["PDV & Vendas", "Estoque"])

if menu == "PDV & Vendas":
    st.subheader("🛒 Carrinho com Desconto")
    
    pesquisa = st.text_input("🔍 Buscar produto:")
    if pesquisa:
        df_f = df[df["Produto"].astype(str).str.contains(pesquisa, case=False, na=False)]
        if not df_f.empty:
            prod = st.selectbox("Selecione:", df_f["Produto"].tolist())
            dados = df_f[df_f["Produto"] == prod].iloc[0]
            
            preco_final = st.number_input("Preço de Venda Final (R$):", value=float(dados["Preco"]), format="%.2f")
            qtd = st.number_input("Quantidade:", min_value=1, value=1)
            
            if st.button("➕ Adicionar ao Carrinho"):
                preco_cheio = preco_final / 0.85
                economia = preco_cheio - preco_final
                st.session_state.carrinho.append({
                    "Produto": prod, "Preco_Final": preco_final, 
                    "Preco_Cheio": preco_cheio, "Economia": economia, "Qtd": qtd
                })
                st.success(f"{prod} adicionado com 15% de desconto!")

    if st.session_state.carrinho:
        total_final = 0
        total_economia = 0
        lista_itens = ""
        
        for i, item in enumerate(st.session_state.carrinho):
            sub = item['Preco_Final'] * item['Qtd']
            total_final += sub
            total_economia += (item['Economia'] * item['Qtd'])
            lista_itens += f"{i+1:02d} | {item['Qtd']}x {item['Produto']}\n"
            lista_itens += f"   De: R$ {item['Preco_Cheio']:.2f} por: R$ {item['Preco_Final']:.2f}\n"
            lista_itens += f"   Economia: R$ {item['Economia']:.2f}\n"

        st.write("---")
        usar_entrega = st.checkbox("🚚 Adicionar taxa de entrega?")
        taxa = st.number_input("Valor da Taxa (R$):", value=5.00) if usar_entrega else 0.0
        
        cliente = st.text_input("Nome do Cliente:")
        whatsapp = st.text_input("WhatsApp (ex: 22999999999):")
        
        if st.button("✅ GERAR NOTA E OPÇÕES"):
            msg = f"FARMA BÚZIOS\nCNPJ: 68.530.976/0001-00\n----------------------------\n"
            msg += f"DATA: {get_brasilia_time().strftime('%d/%m/%Y %H:%M')}\nCLIENTE: {cliente}\n----------------------------\n"
            msg += f"ITENS:\n{lista_itens}----------------------------\n"
            if usar_entrega: msg += f"TAXA DE ENTREGA: R$ {taxa:.2f}\n----------------------------\n"
            msg += f"TOTAL A PAGAR: R$ {total_final + taxa:.2f}\nVOCÊ ECONOMIZOU: R$ {total_economia:.2f}\n============================\nObrigado pela preferência!"
            
            st.code(msg)
            
            link = f"https://wa.me/55{whatsapp}?text={urllib.parse.quote(msg)}"
            st.markdown(f"[🔗 CLIQUE AQUI PARA ENVIAR NO WHATSAPP]({link})")
            
            # Geração do PDF usando FPDF (compatível com o que já está instalado)
            pdf = FPDF(unit="mm", format=(58, 200)) # Formato bobina térmica
            pdf.add_page()
            pdf.set_font("Arial", size=8)
            
            for line in msg.split('\n'):
                # Substitui caracteres especiais para evitar erros de codificação no FPDF padrão
                clean_line = line.encode('latin-1', 'ignore').decode('latin-1')
                pdf.cell(0, 5, txt=clean_line, ln=True)
            
            # Salva o PDF em arquivo temporário para download
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                pdf.output(tmp_file.name)
                tmp_path = tmp_file.name

            with open(tmp_path, "rb") as f:
                pdf_bytes = f.read()
            
            os.unlink(tmp_path)
            
            st.download_button(
                label="📥 BAIXAR NOTINHA EM PDF",
                data=pdf_bytes,
                file_name=f"nota_{cliente}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf"
            )

else:
    st.dataframe(df)
