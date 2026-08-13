import streamlit as st
import pandas as pd
import os
import urllib.parse
from datetime import datetime
from fpdf import FPDF
import pdfplumber

st.set_page_config(page_title="Farma Lagos - Gestão & Pedidos", layout="wide", page_icon="💊")

# Estilização
st.markdown("""
    <style>
    .main-header {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        color: #0E4B82;
        text-align: center;
        padding: 10px 0px 15px 0px;
        font-weight: 800;
        font-size: 2.2rem;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

ARQUIVO_ESTOQUE = "estoque_drogaria.csv"
ARQUIVO_VENDAS = "vendas_historico.csv"
ARQUIVO_CLIENTES = "clientes_drogaria.csv"

# Configurações da Loja
NOME_LOJA = "FARMA LAGOS"
CNPJ_LOJA = "00.000.000/0001-00"  # Insira seu CNPJ oficial aqui, se desejar
ENDERECO_LOJA = "Região dos Lagos, Búzios - RJ"
FILIAL = "Filial 01"

# --- FUNÇÕES DE SALVAMENTO PERMANENTE ---
def salvar_estoque_disco(df_estoque):
    df_estoque.to_csv(ARQUIVO_ESTOQUE, index=False)
    st.cache_data.clear()

def salvar_vendas_disco(df_vendas):
    df_vendas.to_csv(ARQUIVO_VENDAS, index=False)

def salvar_clientes_disco(df_clientes):
    df_clientes.to_csv(ARQUIVO_CLIENTES, index=False)

# --- CARREGAMENTO DE DADOS ---
@st.cache_data
def carregar_estoque_base():
    if os.path.exists(ARQUIVO_ESTOQUE):
        try:
            df = pd.read_csv(ARQUIVO_ESTOQUE)
            df['Descrição'] = df['Descrição'].astype(str)
            df['Quantidade'] = pd.to_numeric(df['Quantidade'], errors='coerce').fillna(0).astype(int)
            df['Preço Unit. (R$)'] = pd.to_numeric(df['Preço Unit. (R$)'], errors='coerce').fillna(0.0)
            if 'Preço Custo (R$)' not in df.columns:
                df['Preço Custo (R$)'] = (df['Preço Unit. (R$)'] * 0.60).round(2)
            return df
        except Exception:
            pass
    return pd.DataFrame(columns=['Descrição', 'Quantidade', 'Preço Unit. (R$)', 'Preço Custo (R$)'])

def carregar_vendas_base():
    if os.path.exists(ARQUIVO_VENDAS):
        try:
            df = pd.read_csv(ARQUIVO_VENDAS)
            if 'Data/Hora' in df.columns:
                df['Data_Obj'] = pd.to_datetime(df['Data/Hora'], format="%d/%m/%Y %H:%M", errors='coerce')
            return df
        except Exception:
            pass
    return pd.DataFrame(columns=['Data/Hora', 'Cliente', 'WhatsApp', 'Produto', 'Qtd', 'Custo Total (R$)', 'Venda Total (R$)', 'Lucro (R$)'])

def carregar_clientes_base():
    if os.path.exists(ARQUIVO_CLIENTES):
        try:
            df = pd.read_csv(ARQUIVO_CLIENTES, dtype={'WhatsApp': str})
            df['WhatsApp'] = df['WhatsApp'].astype(str)
            return df
        except Exception:
            pass
    return pd.DataFrame(columns=['Nome', 'WhatsApp', 'Endereço'])

# --- FUNÇÃO PARA GERAR PDF DE CLIENTES ---
def gerar_pdf_clientes(df_clientes):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Relatorio de Clientes - Farma Lagos", ln=True, align='C')
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(80, 8, "Nome do Cliente", border=1)
    pdf.cell(50, 8, "WhatsApp", border=1)
    pdf.cell(60, 8, "Endereco", border=1)
    pdf.ln()
    
    pdf.set_font("Arial", '', 10)
    for _, row in df_clientes.iterrows():
        nome = str(row['Nome'])[:35]
        whats = str(row['WhatsApp'])
        end = str(row.get('Endereço', ''))[:25]
        
        pdf.cell(80, 7, nome, border=1)
        pdf.cell(50, 7, whats, border=1)
        pdf.cell(60, 7, end, border=1)
        pdf.ln()
        
    return pdf.output(dest='S').encode('latin-1', errors='replace')

# --- EXTRAÇÃO FLEXÍVEL DE PLANILHAS (EXCEL / CSV / PDF) ---
def extrair_clientes_de_arquivo(uploaded_file):
    filename = uploaded_file.name.lower()
    novos = []

    if filename.endswith('.pdf'):
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                tabelas = page.extract_tables()
                for tabela in tabelas:
                    for linha in tabela:
                        if len(linha) >= 2 and linha[0] and "Nome" not in str(linha[0]):
                            nome = str(linha[0]).strip()
                            whats = str(linha[1]).strip()
                            end = str(linha[2]).strip() if len(linha) > 2 and linha[2] else ""
                            if nome:
                                novos.append({'Nome': nome, 'WhatsApp': whats, 'Endereço': end})
        return pd.DataFrame(novos)

    elif filename.endswith(('.xlsx', '.xls', '.csv')):
        if filename.endswith('.csv'):
            df = pd.read_csv(uploaded_file, dtype=str)
        else:
            df = pd.read_excel(uploaded_file, dtype=str)

        col_nome, col_whats, col_end = None, None, None

        for col in df.columns:
            c_lower = str(col).lower().strip()
            if any(k in c_lower for k in ['nome', 'cliente', 'razão', 'pessoa', 'contato']):
                col_nome = col
            elif any(k in c_lower for k in ['whats', 'tel', 'celular', 'fone', 'numero', 'número', 'mobile']):
                col_whats = col
            elif any(k in c_lower for k in ['end', 'rua', 'bairro', 'local', 'endereço', 'endereco']):
                col_end = col

        if not col_nome and len(df.columns) >= 1: col_nome = df.columns[0]
        if not col_whats and len(df.columns) >= 2: col_whats = df.columns[1]
        if not col_end and len(df.columns) >= 3: col_end = df.columns[2]

        df_res = pd.DataFrame()
        df_res['Nome'] = df[col_nome].astype(str).str.strip() if col_nome else ""
        df_res['WhatsApp'] = df[col_whats].astype(str).str.strip() if col_whats else ""
        df_res['Endereço'] = df[col_end].astype(str).str.strip() if col_end else ""

        df_res = df_res[df_res['Nome'].str.lower() != 'nan']
        return df_res

    return pd.DataFrame()

# --- ESTADOS DA SESSÃO ---
if 'estoque' not in st.session_state:
    st.session_state['estoque'] = carregar_estoque_base()

if 'vendas_historico' not in st.session_state:
    st.session_state['vendas_historico'] = carregar_vendas_base()

if 'clientes' not in st.session_state:
    st.session_state['clientes'] = carregar_clientes_base()

if 'carrinho' not in st.session_state:
    st.session_state['carrinho'] = []

st.markdown(f"<h1 class='main-header'>💊 {NOME_LOJA}</h1>", unsafe_allow_html=True)
st.caption(f"CNPJ: {CNPJ_LOJA} | {ENDERECO_LOJA} | {FILIAL}")

menu = st.radio(
    "Navegação",
    ["🛒 Emitir Pedido", "👥 Clientes & Alertas", "📋 Estoque & Preços", "📈 Lucros & Metas", "➕ Novo Produto"],
    horizontal=True,
    key="menu_principal"
)

st.divider()

# ==================== ABA 1: EMITIR PEDIDO & CARRINHO ====================
if menu == "🛒 Emitir Pedido":
    st.header("🛒 Emitir Pedido / Cupom Fiscal")
    
    cli_sel = st.session_state.pop('cliente_para_pedido', None)
    
    if st.session_state['estoque'].empty:
        st.warning("⚠️ O estoque está vazio no momento. Cadastre produtos na aba 'Novo Produto'.")
    else:
        col_busca, col_carrinho = st.columns([1, 1])
        
        with col_busca:
            st.subheader("1. Selecionar Medicamentos")
            busca = st.text_input("🔍 Digite o nome do produto para buscar:", "", key="busca_prod")
            
            df_estoque = st.session_state['estoque']
            
            if busca.strip():
                resultados = df_estoque[df_estoque['Descrição'].str.contains(busca, case=False, na=False)]
            else:
                resultados = df_estoque.head(20)
            
            if resultados.empty:
                st.info("Nenhum produto encontrado.")
            else:
                opcoes_produtos = resultados['Descrição'].tolist()
                prod_selecionado = st.selectbox("Selecione o produto da lista:", opcoes_produtos, key="select_prod")
                
                item_info = df_estoque[df_estoque['Descrição'] == prod_selecionado].iloc[0]
                preco_base = float(item_info['Preço Unit. (R$)'])
                preco_custo = float(item_info.get('Preço Custo (R$)', preco_base * 0.6))
                qtd_disp = int(item_info['Quantidade'])
                
                st.info(f"💡 **Preço Cadastrado:** R$ {preco_base:.2f} | **Estoque Atual:** {qtd_disp} un")
                
                col_p, col_q = st.columns(2)
                with col_p:
                    preco_venda = st.number_input("Preço de Venda (R$):", min_value=0.0, value=preco_base, format="%.2f", key="preco_venda")
                with col_q:
                    qtd_pedir = st.number_input("Qtd Desejada:", min_value=1, max_value=max(1, qtd_disp), value=1, step=1, key="qtd_pedir")
                
                if st.button("➕ Adicionar ao Carrinho", use_container_width=True, type="primary"):
                    st.session_state['carrinho'].append({
                        'Descrição': prod_selecionado,
                        'Qtd': qtd_pedir,
                        'Custo Unit. (R$)': preco_custo,
                        'Preço Unit. (R$)': preco_venda,
                        'Subtotal (R$)': round(qtd_pedir * preco_venda, 2),
                        'Custo Subtotal (R$)': round(qtd_pedir * preco_custo, 2)
                    })
                    st.success("Adicionado ao carrinho!")

            st.divider()
            st.subheader("2. Dados do Cliente & Entrega")
            
            val_nome = cli_sel['Nome'] if cli_sel else ""
            val_whats = cli_sel['WhatsApp'] if cli_sel else ""
            val_end = cli_sel['Endereço'] if cli_sel else ""

            nome_cliente = st.text_input("👤 Nome do Cliente:", value=val_nome, key="nome_cliente")
            cpf_cliente = st.text_input("📄 CPF / CNPJ do Cliente (Opcional para Nota):", value="", key="cpf_cliente")
            whatsapp_cliente = st.text_input("📱 WhatsApp do Cliente (com DDD):", value=val_whats, placeholder="22999999999", key="whatsapp_cliente")
            endereco_cliente = st.text_area("📍 Endereço Completo de Entrega:", value=val_end, key="endereco_cliente")
            
            cobrar_taxa = st.checkbox("🛵 Incluir taxa de entrega / Motoboy?", key="cobrar_taxa")
            taxa_motoboy = 0.0
            if cobrar_taxa:
                taxa_motoboy = st.number_input("Valor da Taxa (R$):", min_value=2.0, max_value=100.0, value=5.0, step=0.5, key="taxa_motoboy")

        with col_carrinho:
            st.subheader("3. Resumo & Nota Fiscal")
            
            if not st.session_state['carrinho']:
                st.info("O carrinho está vazio no momento.")
            else:
                df_carrinho = pd.DataFrame(st.session_state['carrinho'])
                st.dataframe(df_carrinho[['Descrição', 'Qtd', 'Preço Unit. (R$)', 'Subtotal (R$)']], use_container_width=True)
                
                subtotal_produtos = df_carrinho['Subtotal (R$)'].sum()
                total_geral = subtotal_produtos + taxa_motoboy
                
                st.write(f"Subtotal dos Produtos: **R$ {subtotal_produtos:.2f}**")
                if cobrar_taxa:
                    st.write(f"Taxa do Motoboy: **R$ {taxa_motoboy:.2f}**")
                st.markdown(f"### **Total do Pedido: R$ {total_geral:.2f}**")
                
                if st.button("✅ Confirmar Venda & Salvar", use_container_width=True, type="primary"):
                    dt_atual = datetime.now()
                    data_hora_str = dt_atual.strftime("%d/%m/%Y %H:%M")
                    
                    novas_vendas = []
                    for item in st.session_state['carrinho']:
                        desc = item['Descrição']
                        qtd_vendid = item['Qtd']
                        idx = st.session_state['estoque'][st.session_state['estoque']['Descrição'] == desc].index
                        
                        if not idx.empty:
                            nova_qtd = max(0, st.session_state['estoque'].loc[idx, 'Quantidade'].values[0] - qtd_vendid)
                            st.session_state['estoque'].loc[idx, 'Quantidade'] = nova_qtd
                        
                        custo_tot = item['Custo Subtotal (R$)']
                        venda_tot = item['Subtotal (R$)']
                        novas_vendas.append({
                            'Data/Hora': data_hora_str,
                            'Cliente': nome_cliente if nome_cliente else 'Cliente Balcão',
                            'WhatsApp': whatsapp_cliente,
                            'Produto': desc,
                            'Qtd': qtd_vendid,
                            'Custo Total (R$)': custo_tot,
                            'Venda Total (R$)': venda_tot,
                            'Lucro (R$)': round(venda_tot - custo_tot, 2)
                        })
                    
                    if nome_cliente.strip() and whatsapp_cliente.strip():
                        df_cli = st.session_state['clientes']
                        exists = df_cli[df_cli['WhatsApp'].astype(str) == str(whatsapp_cliente)]
                        if exists.empty:
                            novo_c = pd.DataFrame([{'Nome': nome_cliente.strip(), 'WhatsApp': str(whatsapp_cliente).strip(), 'Endereço': endereco_cliente.strip()}])
                            st.session_state['clientes'] = pd.concat([df_cli, novo_c], ignore_index=True)
                            salvar_clientes_disco(st.session_state['clientes'])

                    salvar_estoque_disco(st.session_state['estoque'])
                    st.session_state['vendas_historico'] = pd.concat([st.session_state['vendas_historico'], pd.DataFrame(novas_vendas)], ignore_index=True)
                    salvar_vendas_disco(st.session_state['vendas_historico'])
                    
                    st.session_state['carrinho'] = []
                    st.success("Venda gravada! Estoque atualizado e contato salvo com sucesso.")
                    st.rerun()

                # --- NOTA FISCAL / CUPOM FISCAL ELETRÔNICO CONFIGURADO ---
                data_hora_nf = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                texto_nf = f"""========================================
{NOME_LOJA} - {FILIAL}
CNPJ: {CNPJ_LOJA}
Endereço: {ENDERECO_LOJA}
========================================
EXTRATO Nº {datetime.now().strftime("%H%M%S")} - CUPOM FISCAL ELETRÔNICO
Data: {data_hora_nf}
----------------------------------------
CLIENTE: {nome_cliente if nome_cliente else "Consumidor"}
CPF/CNPJ: {cpf_cliente if cpf_cliente else "Não informado"}
----------------------------------------
QTD | ITEM                        | TOTAL
"""
                for _, row in df_carrinho.iterrows():
                    item_nome = str(row['Descrição'])[:25]
                    texto_nf += f"{row['Qtd']}   | {item_nome:<27} | R$ {row['Subtotal (R$)']:.2f}\n"
                
                if cobrar_taxa:
                    texto_nf += f"1   | Taxa de Entrega / Motoboy      | R$ {taxa_motoboy:.2f}\n"
                
                texto_nf += f"----------------------------------------\n"
                texto_nf += f"VALOR TOTAL A PAGAR           | R$ {total_geral:.2f}\n"
                texto_nf += f"========================================\n"
                texto_nf += f"Obrigado pela preferência! Volte sempre."

                st.text_area("📄 Visualização da Nota Fiscal:", value=texto_nf, height=220)

                if whatsapp_cliente:
                    fone_limpo = ''.join(filter(str.isdigit, whatsapp_cliente))
                    msg_encoded = urllib.parse.quote(texto_nf)
                    st.link_button("📲 Enviar Nota Fiscal via WhatsApp", f"https://api.whatsapp.com/send?phone=55{fone_limpo}&text={msg_encoded}", use_container_width=True)

                if st.button("🗑️ Limpar Carrinho", use_container_width=True):
                    st.session_state['carrinho'] = []
                    st.rerun()

# ==================== ABA 2: CLIENTES & ALERTAS DE RECOMPRA ====================
elif menu == "👥 Clientes & Alertas":
    st.header("👥 Gestão de Clientes & Alerta de Recompra (28 dias)")
    
    df_clientes = st.session_state['clientes']
    df_vendas = st.session_state['vendas_historico']
    
    st.subheader("🔔 Lembrete Automático de Recompra (Uso Contínuo)")
    if not df_vendas.empty and 'Data_Obj' in df_vendas.columns:
        hoje = datetime.now()
        df_vendas_validas = df_vendas.dropna(subset=['Data_Obj'])
        
        ultimas_compras = df_vendas_validas.groupby(['Cliente', 'WhatsApp', 'Produto'])['Data_Obj'].max().reset_index()
        
        alertas = []
        for _, row in ultimas_compras.iterrows():
            dias_decorridos = (hoje - row['Data_Obj']).days
            if dias_decorridos >= 28:
                alertas.append({
                    'Cliente': row['Cliente'],
                    'WhatsApp': row['WhatsApp'],
                    'Último Medicamento': row['Produto'],
                    'Dias desde a compra': dias_decorridos,
                    'Data da Compra': row['Data_Obj'].strftime("%d/%m/%Y")
                })
        
        if alertas:
            df_alertas = pd.DataFrame(alertas)
            st.warning(f"⚠️ **{len(df_alertas)} cliente(s)** compraram remédios há 28 dias ou mais e podem precisar renovar o estoque!")
            
            for _, alt in df_alertas.iterrows():
                col_a1, col_a2, col_a3 = st.columns([2, 2, 1])
                with col_a1:
                    st.write(f"👤 **{alt['Cliente']}** ({alt['Último Medicamento']})")
                with col_a2:
                    st.write(f"📅 Compra feita há **{alt['Dias desde a compra']} dias** ({alt['Data da Compra']})")
                with col_a3:
                    if alt['WhatsApp'] and str(alt['WhatsApp']).strip() != 'nan':
                        fone = ''.join(filter(str.isdigit, str(alt['WhatsApp'])))
                        msg = urllib.parse.quote(f"Olá {alt['Cliente']}, tudo bem? Notamos que faz cerca de 1 mês que você adquiriu o medicamento {alt['Último Medicamento']}. Gostaria de renovar seu pedido com a {NOME_LOJA}?")
                        st.link_button("📲 Cobrar Recompra", f"https://api.whatsapp.com/send?phone=55{fone}&text={msg}")
            st.divider()
        else:
            st.success("✅ Nenhuma pendência de recompra registrada para os últimos 28 dias.")
    
    col_c1, col_c2 = st.columns([2, 1])
    
    with col_c1:
        st.subheader("📋 Lista de Clientes Cadastrados")
        if df_clientes.empty:
            st.info("Nenhum cliente cadastrado ainda.")
        else:
            for idx, row in df_clientes.iterrows():
                c_box = st.container()
                with c_box:
                    col_info, col_btn = st.columns([3, 1])
                    with col_info:
                        st.write(f"👤 **{row['Nome']}** | 📱 WhatsApp: {row['WhatsApp']}")
                        if row.get('Endereço'):
                            st.caption(f"📍 {row['Endereço']}")
                    with col_btn:
                        if st.button("🛒 Iniciar Pedido", key=f"btn_ped_{idx}"):
                            st.session_state['cliente_para_pedido'] = row.to_dict()
                            st.success(f"Cliente {row['Nome']} selecionado! Vá para a aba 'Emitir Pedido'.")

    with col_c2:
        st.subheader("📤 Importar Lista de Clientes")
        arquivo_cli = st.file_uploader("Selecione o arquivo Excel (Pasta2.xlsx), PDF ou CSV:", type=['xlsx', 'xls', 'pdf', 'csv'], key="upload_clientes")
        
        if arquivo_cli is not None:
            if st.button("📥 Processar e Importar Clientes", type="primary", use_container_width=True):
                try:
                    novos_df = extrair_clientes_de_arquivo(arquivo_cli)
                    if not novos_df.empty:
                        st.session_state['clientes'] = pd.concat([st.session_state['clientes'], novos_df], ignore_index=True).drop_duplicates(subset=['WhatsApp'])
                        salvar_clientes_disco(st.session_state['clientes'])
                        st.success(f"✅ Sucesso! {len(novos_df)} clientes processados e salvos!")
                        st.rerun()
                    else:
                        st.error("⚠️ Não encontramos dados válidos de clientes nesta planilha.")
                except Exception as e:
                    st.error(f"Erro na leitura do arquivo: {e}.")

        st.divider()
        st.subheader("📥 Exportar Contatos")
        if not df_clientes.empty:
            pdf_bytes = gerar_pdf_clientes(df_clientes)
            st.download_button(
                label="📄 Baixar Lista em PDF",
                data=pdf_bytes,
                file_name="clientes_farma_lagos.pdf",
                mime="application/pdf",
                use_container_width=True
            )

# ==================== ABA 3: ESTOQUE & PREÇOS ====================
elif menu == "📋 Estoque & Preços":
    st.header("📋 Gestão de Estoque & Precificação")
    
    df_estoque = st.session_state['estoque']
    
    if df_estoque.empty:
        st.info("Nenhum produto cadastrado no estoque.")
    else:
        pesquisa_est = st.text_input("🔍 Pesquisar produto no estoque:", "")
        df_est_filtrado = df_estoque.copy()
        if pesquisa_est.strip():
            df_est_filtrado = df_estoque[df_estoque['Descrição'].str.contains(pesquisa_est, case=False, na=False)]
        
        st.subheader("Alterar Preços e Quantidades em Tempo Real")
        
        edited_df = st.data_editor(
            df_est_filtrado,
            num_rows="dynamic",
            use_container_width=True,
            key="editor_estoque"
        )
        
        if st.button("💾 Salvar Alterações do Estoque", type="primary"):
            st.session_state['estoque'] = edited_df
            salvar_estoque_disco(edited_df)
            st.success("✅ Estoque e preços atualizados com sucesso!")
            st.rerun()
            
        csv_est = df_estoque.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Baixar Estoque em CSV", data=csv_est, file_name="estoque_farma_lagos.csv", mime="text/csv", use_container_width=True)

# ==================== ABA 4: LUCROS & METAS ====================
elif menu == "📈 Lucros & Metas":
    st.header("📈 Relatório de Vendas, Lucros & Metas")
    
    df_vendas = st.session_state['vendas_historico']
    
    if df_vendas.empty:
        st.info("Nenhuma venda registrada até o momento.")
    else:
        col_m1, col_m2, col_m3 = st.columns(3)
        total_faturado = df_vendas['Venda Total (R$)'].sum()
        total_lucro = df_vendas['Lucro (R$)'].sum()
        total_itens_vendidos = df_vendas['Qtd'].sum()
        
        with col_m1:
            st.metric("💰 Faturamento Total", f"R$ {total_faturado:.2f}")
        with col_m2:
            st.metric("📊 Lucro Total Estimado", f"R$ {total_lucro:.2f}")
        with col_m3:
            st.metric("📦 Total de Itens Vendidos", f"{total_itens_vendidos} un")
            
        st.divider()
        st.subheader("📋 Histórico Completo de Vendas")
        st.dataframe(df_vendas, use_container_width=True)
        
        csv_vendas = df_vendas.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Baixar Relatório de Vendas (CSV)", data=csv_vendas, file_name="vendas_farma_lagos.csv", mime="text/csv")

# ==================== ABA 5: NOVO PRODUTO ====================
elif menu == "➕ Novo Produto":
    st.header("➕ Cadastrar Novo Produto")
    
    with st.form("form_novo_produto"):
        desc_novo = st.text_input("Descrição / Nome do Medicamento:")
        qtd_novo = st.number_input("Quantidade Inicial em Estoque:", min_value=0, value=10, step=1)
        preco_venda_novo = st.number_input("Preço de Venda Unitário (R$):", min_value=0.0, value=10.0, format="%.2f")
        preco_custo_novo = st.number_input("Preço de Custo Unitário (R$):", min_value=0.0, value=6.0, format="%.2f")
        
        cadastrar_btn = st.form_submit_button("Cadastrar Produto", use_container_width=True)
        
        if cadastrar_btn:
            if desc_novo.strip():
                novo_item = pd.DataFrame([{
                    'Descrição': desc_novo.strip(),
                    'Quantidade': int(qtd_novo),
                    'Preço Unit. (R$)': float(preco_venda_novo),
                    'Preço Custo (R$)': float(preco_custo_novo)
                }])
                st.session_state['estoque'] = pd.concat([st.session_state['estoque'], novo_item], ignore_index=True)
                salvar_estoque_disco(st.session_state['estoque'])
                st.success(f"✅ Produto '{desc_novo}' cadastrado com sucesso!")
            else:
                st.warning("⚠️ Insira uma descrição válida para o produto.")
