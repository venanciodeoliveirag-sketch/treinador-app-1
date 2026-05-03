import streamlit as st
from datetime import datetime, timedelta
import urllib.parse
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import os

# ==================================================
# --- TRADUTOR DE MESES (ÁREA DO PROFESSOR) ---
# ==================================================
MESES_PT = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

# ==================================================
# --- 1. CONFIGURAÇÃO VISUAL (NOVO ESTILO AZUL) ---
# ==================================================
st.set_page_config(
    page_title="Agenda de Personal", 
    page_icon="💪", 
    layout="centered"
)

# Cores atualizadas para combinar com o logotipo (Azul e Preto)
st.markdown("""
<style>
    .stApp { background-color: #000000; color: #FFFFFF; }
    h1, h2, h3, b { color: #0056b3 !important; } /* Azul do Logotipo */
    .stButton>button { background-color: #0056b3; color: white; border: none; font-weight: bold; border-radius: 10px; transition: all 0.3s; }
    .stButton>button:hover { background-color: #FFFFFF; color: #0056b3; transform: scale(1.05); }
    .stDateInput div, .stSelectbox div, .stTextInput div { color: black !important; }
    .vitrine-container { display: flex; justify-content: space-between; padding: 15px; border-radius: 15px; overflow-x: auto; background-color: #111111; border: 1px solid #333333; }
</style>
""", unsafe_allow_html=True)


# ==================================================
# --- 2. BANCO DE DADOS E CONEXÃO ---
# ==================================================
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    return conn.read(ttl=0, usecols=[0, 1, 2]).dropna(how="all")

def salvar_agendamento(data_str, hora, nome):
    df_existente = carregar_dados()
    if not df_existente.empty and "Data" in df_existente.columns and "Hora" in df_existente.columns:
        conflito = df_existente[(df_existente["Data"] == data_str) & (df_existente["Hora"] == hora)]
    else:
        conflito = pd.DataFrame()
    
    if conflito.empty:
        novo_registro = pd.DataFrame([{"Data": data_str, "Hora": hora, "Nome": nome}])
        df_atualizado = pd.concat([df_existente, novo_registro], ignore_index=True)
        conn.update(data=df_atualizado) 
        return True
    return False

# ==================================================
# --- 3. CONFIGURAÇÃO DA ESCALA 2x2 ---
# ==================================================
DATA_REFERENCIA = datetime(2026, 5, 4).date()
SEU_WHATSAPP = "5528999896258"

def verificar_disponibilidade(data):
    if data.weekday() == 6:
        return "Domingo - Folga Fixa", False
    delta_dias = (data - DATA_REFERENCIA).days
    posicao = delta_dias % 4
    if posicao in [0, 1]:
        return "Plantão PM (Indisponível)", False
    else:
        return "Disponível para Personal", True


# ==================================================
# --- 4. TÍTULO E VITRINE (COM SEU LOGOTIPO) ---
# ==================================================
nome_imagem = "logo.jpg"

if os.path.exists(nome_imagem):
    col1, col2, col3 = st.columns([1, 2, 1]) 
    with col2:
        # Imagem com bordas arredondadas e fundo branco para destacar no app preto
        st.markdown(f'<div style="background-color:white; padding:10px; border-radius:15px; text-align:center;"><img src="https://raw.githubusercontent.com/GuilhermeVenancio/AQUI_VAI_O_NOME_DO_SEU_REPOSITORIO/main/logo.jpg" width="100%" style="border-radius:10px;"></div>', unsafe_allow_html=True)
        st.image(nome_imagem, use_container_width=True)
else:
    st.warning(f"⚠️ Imagem '{nome_imagem}' não encontrada no repositório do GitHub.")

st.write("<br>", unsafe_allow_html=True)
st.write("Verifique a minha disponibilidade abaixo e faça o seu check-in.")
st.write("### 📅 Previsão da Semana")

html_vitrine = "<div class='vitrine-container'>"
hoje = datetime.today().date()

for i in range(7):
    dia_previsao = hoje + timedelta(days=i)
    _, disponivel_prev = verificar_disponibilidade(dia_previsao)
    dia_semana_abrev = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"][dia_previsao.weekday()]
    
    if not disponivel_prev:
        icone = "🏖️" if dia_previsao.weekday() == 6 else "🚔"
    else:
        icone = "✅"
        
    html_vitrine += f"""
        <div style='text-align: center; min-width: 45px; margin: 0 5px;'>
            <b style='font-size: 14px;'>{dia_semana_abrev}</b><br>
            <span style='font-size: 11px; color: gray;'>{dia_previsao.strftime('%d/%m')}</span><br>
            <span style='font-size: 26px;'>{icone}</span>
        </div>
    """

html_vitrine += "</div>"
html_vitrine_limpo = html_vitrine.replace("\n", "")
st.markdown(html_vitrine_limpo, unsafe_allow_html=True)
st.divider()

# ==================================================
# --- 5. INTERFACE DE AGENDAMENTO ---
# ==================================================
data_selecionada = st.date_input("1️⃣ Selecione a data no calendário:", min_value=datetime.today(), format="DD/MM/YYYY")

status_dia, disponivel_dia = verificar_disponibilidade(data_selecionada)

if not disponivel_dia:
    st.markdown(f"<div style='padding: 10px; border-radius: 10px; background-color: #440000; color: white; border: 1px solid red;'>🚫 {status_dia}</div>", unsafe_allow_html=True)
    st.info("Por favor, escolha um dia marcado com ✅ na previsão acima.")
else:
    st.markdown(f"<div style='padding: 10px; border-radius: 10px; background-color: #003300; color: white; border: 1px solid #00FF00;'>✅ {status_dia}</div>", unsafe_allow_html=True)
    st.write("")
    
    df_agendamentos = carregar_dados()
    data_str = data_selecionada.strftime("%Y-%m-%d")
    
    if not df_agendamentos.empty and "Data" in df_agendamentos.columns and "Hora" in df_agendamentos.columns:
        ocupados = df_agendamentos[df_agendamentos["Data"] == data_str]["Hora"].tolist()
    else:
        ocupados = []
        
    horarios_padrao = ["05:00", "06:00", "07:00", "08:00", "09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00"]
    horarios_livres = [h for h in horarios_padrao if h not in ocupados]
    
    if not horarios_livres:
        st.warning("Poxa, todos os horários para este dia já foram preenchidos! 😢")
    else:
        hora = st.selectbox("2️⃣ Escolha o horário disponível:", horarios_livres)
        nome = st.text_input("3️⃣ Digite o seu nome completo:")

        st.write("")
        if st.button("CONFIRMAR CHECK-IN 💪", use_container_width=True):
            if nome:
                if salvar_agendamento(data_str, hora, nome):
                    msg = f"Olá! Sou o aluno *{nome}* e fiz check-in para o treino no dia *{data_selecionada.strftime('%d/%m')}* às *{hora}*."
                    link_wa = f"https://wa.me/{SEU_WHATSAPP}?text={urllib.parse.quote(msg)}"
                    
                    st.balloons() 
                    st.success("Horário reservado com sucesso!")
                    
                    st.markdown(f'''
                        <a href="{link_wa}" target="_blank">
                            <button style="width:100%;height:60px;border-radius:15px;background-color:#25d366;color:white;border:none;font-size:18px;font-weight:bold;cursor:pointer;box-shadow: 0 4px 15px rgba(0,255,0,0.3);">
                                📱 NOTIFICAR NO WHATSAPP
                            </button>
                        </a>
                    ''', unsafe_allow_html=True)
                    st.cache_data.clear()
                else:
                    st.error("Erro: Este horário acabou de ser preenchido por outra pessoa.")
            else:
                st.warning("Por favor, digite o seu nome antes de confirmar.")


# ==================================================
# --- 6. ÁREA DO PROFESSOR (RELATÓRIO DE FREQUÊNCIA) ---
# ==================================================
st.write("<br><br>", unsafe_allow_html=True) 
st.divider()

with st.expander("📊 Relatório de Frequência (Área Restrita)"):
    senha = st.text_input("Senha de acesso:", type="password")
    if senha == "1234":
        st.success("Acesso Liberado!")
        
        df_relatorio = carregar_dados()
        if not df_relatorio.empty:
            df_relatorio['Data'] = pd.to_datetime(df_relatorio['Data'])
            mes_atual = datetime.now().month
            ano_atual = datetime.now().year
            df_mes = df_relatorio[(df_relatorio['Data'].dt.month == mes_atual) & (df_relatorio['Data'].dt.year == ano_atual)]
            
            if not df_mes.empty:
                contagem = df_mes['Nome'].value_counts().reset_index()
                contagem.columns = ['Aluno', 'Aulas no Mês']
                
                nome_do_mes_pt = MESES_PT[mes_atual - 1]
                st.write(f"### 📈 Resumo de {nome_do_mes_pt} de {ano_atual}")
                
                st.dataframe(contagem, use_container_width=True)
                
                st.write("---")
                st.write("🔍 **Histórico Detalhado:**")
                st.dataframe(df_mes.sort_values(by='Data', ascending=False), use_container_width=True)
            else:
                st.info("Ainda não há check-ins registrados neste mês.")
        else:
            st.info("A planilha ainda está vazia.")
    elif senha != "":
        st.error("Senha incorreta.")
