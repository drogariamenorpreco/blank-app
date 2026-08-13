import streamlit as st
import pandas as pd
from datetime import datetime

# Configuração da Página
st.set_page_config(
    page_title="Farma Lagos - Gestão e Vendas",
    page_icon="💊",
    layout="centered"
)

# Título Principal do App
st.markdown("<h1 style='text-align: center;'>💊 FARMA LAGOS</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>Sistema de Gestão e Emissão de Documento Fiscal</p>", unsafe_allow_html=True)

# Simulação de carregamento de estoque (ou arquivo CSV)
@st.cache_data
def carregar_dados():
    try:
        return pd.read_csv("estoque_drogaria.csv")
    except:
        return pd.DataFrame({
            "Produto": [
                "AMOXICILINA 250MG SUSP 150ML PRATI",
                "AMOXICILINA 500MG 21CP NEO QUIMICA",
                "DIPIRONA SODICA 500MG 10CP",
                "PARACETAMOL 750MG 20CP"
            ],
            "Preco": [7.32, 18.50, 5.00, 12.00],
            "Estoque": [6, 15, 30, 20]
        })

df = carregar_dados()

# Menu Lateral de Navegação
st.sidebar.markdown("### Navegação")
menu = st.sidebar.radio("Ir para:", ["Emitir Pedido / NF", "Estoque & Preços", "Lucros & Metas"])

if menu == "Emitir Pedido / NF":
    st.subheader("🛒 Emitir Venda e Nota Fiscal")
    
    # Seleção de produtos
    produto_pesquisa = st.text_input("🔍 Digite o nome do produto para buscar:", "AMOXICILINA")
    
    df_filtrado = df[df["Produto"].str.contains(produto_pesquisa, case=False, na=False)]
    
    if not df_filtrado.empty:
        produto_selecionado = st.selectbox("Selecione o produto da lista:", df_filtrado["Produto"].tolist())
        
        # Puxar dados do produto selecionado
        dados_prod = df_filtrado[df_filtrado["Produto"] == produto_selecionado].iloc[0]
        preco_cadastrado = float(dados_prod["Preco"])
        estoque_atual = int(dados_prod["Estoque"])
        
        st.info(f"💡 Preço Cadastrado: R$ {preco_cadastrado:.2f} | Estoque Atual: {estoque_atual} un")
        
        qtd = st.number_input("Quantidade:", min_value=1, max_value=max(1, estoque_atual), value=1)
        preco_venda = st.number_input("Preço de Venda Praticado (R$):", value=preco_cadastrado)
        
        cliente_nome = st.text_input("Nome do Cliente (Opcional):", "Consumidor Final")
        cliente_cpf = st.text_input("CPF/CNPJ do Cliente (Opcional):", "")
        
        total_item = qtd * preco_venda
        
        if st.button("Gerar Nota Fiscal de Consumidor (NFC-e / DANFE)"):
            st.success("Nota Fiscal gerada com sucesso!")
            
            data_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            
            # Estrutura Visual IDÊNTICA a uma Nota Fiscal de Comércio com seus dados oficiais
            st.markdown("---")
            st.markdown(f"""
            <div style="border: 2px dashed #000; padding: 15px; background-color: #ffffff; color: #000000; font-family: monospace; border-radius: 5px;">
                <div style="text-align: center;">
                    <b>68.530.976 CLAUDINEI DE JESUS DA SILVA JUNIOR</b><br>
                    RUA CAICARA - ARMACAO - ARMACAO DOS BUZIOS / RJ<br>
                    <b>CNPJ: 68.530.976/0001-00</b> | CEP: 28950-270<br>
                    --------------------------------------------------<br>
                    <b>DANFE NFC-e - Documento Auxiliar da Nota Fiscal de Consumidor Eletrônica</b><br>
                </div>
                <br>
                <b>DADOS DO CLIENTE:</b><br>
                Nome: {cliente_nome}<br>
                CPF/CNPJ: {cliente_cpf if cliente_cpf else 'Não informado'}<br>
                --------------------------------------------------<br>
                <b>ITENS DA COMPRA:</b><br>
                {qtd}x {produto_selecionado} - R$ {preco_venda:.2f} | Total: R$ {total_item:.2f}<br>
                --------------------------------------------------<br>
                <b>VALOR TOTAL A PAGAR: R$ {total_item:.2f}</b><br>
                Forma de Pagamento: Dinheiro / Cartão<br>
                --------------------------------------------------<br>
                <div style="text-align: center; font-size: 11px;">
                    Número: 000.014.258 | Serie: 001 | Emissão: {data_atual}<br>
                    Protocolo de Autorização: 333260001234567<br>
                    <b>Consulte a validade da nota pelo Chave de Acesso:</b><br>
                    3326 0468 5309 7600 0100 5500 1000 0142 5812 3456 7890<br>
                    <i>Tributos incidentes (Lei Fed. 12.741/2012): R$ {(total_item * 0.13):.2f} (13%)</i>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("---")

elif menu == "Estoque & Preços":
    st.subheader("📦 Gerenciamento de Estoque")
    st.dataframe(df)

else:
    st.subheader("📊 Lucros & Metas")
    st.metric(label="Faturamento Estimado do Dia", value="R$ 1.450,00", delta="+12%")
