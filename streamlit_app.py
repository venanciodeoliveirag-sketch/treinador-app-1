import streamlit as st
from datetime import datetime, timedelta
import urllib.parse
from streamlit_gsheets import GSheetsConnection
import pandas as pd

#
==================================================
# --- 1. CONFIGURAÇÃO VISUAL (ESTILO BLACK & GOLD) ---
#
==================================================
# Mantemos a logomarca aqui na "cara externa" (aba do navegador)
st.set_page_config(
    page_title="Agenda de Personal", 
    page_icon="Treino.jpg", 
    layout="centered"
)

# Injetamos CSS personalizado para mudar as cores do app para Preto e Dourado
st.markdown("""
<style>
    /* Cor de fundo e texto principal */
    .stApp {
        background-color: #000000;
        color: #FFFFFF;
    }
    
    /* Cor dos títulos */
    h1, h2, h3, b {
        color: #D4AF37 !important; /* Dourado */
    }
    
    /* Estilização dos botões padrão */
    .stButton>button {
        background-color: #D4AF37;
        color: black;
        border: none;
        font-weight: bold;
        border-radius: 10px;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #FFFFFF;
        color: black;
        transform: scale(1.05);
    }
    
    /* Inputs e Selectbox */
    .stDateInput div, .stSelectbox div, .stTextInput div {
        color: black !important;
    }

    /* Vitrine da Semana */
    .vitrine-container {
        display: flex; 
        justify-content: space-between; 
        padding: 15px; 
        border-radius: 15px; 
        overflow-x: auto; 
        background-color: #111111; 
        border: 1px solid #333333;
    }
</style>
""", unsafe_allow_html=True)


# --- CONEXÃO COM GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    """Lê os dados da planilha em tempo real"""
    return conn.read(ttl=0, usecols=[0, 1, 2]).dropna(how="all")

def salvar_agendamento(data_str, hora, nome):
    """Verifica conflitos e salva o novo agendamento na planilha"""
    df_existente = carregar_dados()
    
    # Verifica se já existe alguém nesse horário
    if not df_existente.empty and "Data" in df_existente.columns and "Hora" in df_existente.columns:
        conflito = df_existente[(df_existente["Data"] == data_str) & (df_existente["Hora"] == hora)]
    else:
        conflito = pd.DataFrame()
    
    if conflito.empty:
        novo_registro = pd.DataFrame([{"Data": data_str, "Hora": hora, "Nome": nome}])
        df_atualizado = pd.concat([df_existente, novo_registro], ignore_index=True)
        # Envia a atualização para o Google Sheets
        conn.update(data=df_atualizado) 
        return True
    return False

# --- CONFIGURAÇÃO DA ESCALA 2x2 ---
# (Assumindo que Treino.jpg já foi renomeado e está na raiz do GitHub)
DATA_REFERENCIA = datetime(2026, 5, 4).date()
SEU_WHATSAPP = "5528999896258"

def verificar_disponibilidade(data):
    """Calcula se você está de plantão ou disponível"""
    if data.weekday() == 6:
        return "Domingo - Folga Fixa", False
    
    delta_dias = (data - DATA_REFERENCIA).days
    posicao = delta_dias % 4
    
    if posicao in [0, 1]:
        return "Plantão PM (Indisponível)", False
    else:
        return "Disponível para Personal", True

# ==================================================
# --- TÍTULO E VITRINE (SEM IMAGEM INTERNA) ---
# ==================================================
# Retirado st.image(...) a pedido do usuário.

st.title("💪 Agenda de Treinos")
st.write("Verifique a minha disponibilidade abaixo e faça o seu check-in.")

st.write("### 📅 Previsão da Semana")

# HTML/CSS para a vitrine (com estilo dark)
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
st.markdown(html_vitrine, unsafe_allow_html=True)
st.divider()

# ==================================================
# --- INTERFACE DE AGENDAMENTO ---
# ==================================================
data_selecionada = st.date_input("1️⃣ Selecione a data no calendário:", min_value=datetime.today(), format="DD/MM/YYYY")

status_dia, disponivel_dia = verificar_disponibilidade(data_selecionada)

if not disponivel_dia:
    # Cores personalizadas para os alertas no modo Dark
    st.markdown(f"<div style='padding: 10px; border-radius: 10px; background-color: #440000; color: white; border: 1px solid red;'>🚫 {status_dia}</div>", unsafe_allow_html=True)
    st.info("Por favor, escolha um dia marcado com ✅ na previsão acima.")
else:
    # Cores personalizadas para o sucesso no modo Dark
    st.markdown(f"<div style='padding: 10px; border-radius: 10px; background-color: #003300; color: white; border: 1px solid #00FF00;'>✅ {status_dia}</div>", unsafe_allow_html=True)
    st.write("")
    
    # Carregar agendamentos já feitos
    df_agendamentos = carregar_dados()
    data_str = data_selecionada.strftime("%Y-%m-%d")
    
    if not df_agendamentos.empty and "Data" in df_agendamentos.columns and "Hora" in df_agendamentos.columns:
        ocupados = df_agendamentos[df_agendamentos["Data"] == data_str]["Hora"].tolist()
    else:
        ocupados = []
        
    horarios_padrao = ["06:00", "07:00", "08:00", "09:00", "19:00", "20:00", "21:00"]
    horarios_livres = [h for h in horarios_padrao if h not in ocupados]
    
    if not horarios_livres:
        st.warning("Poxa, todos os horários para este dia já foram preenchidos! 😢")
    else:
        hora = st.selectbox("2️⃣ Escolha o horário disponível:", horarios_livres)
        nome = st.text_input("3️⃣ Digite o seu nome completo:")

        st.write("")
        # Botão centralizado e estilizado via CSS no topo
        if st.button("CONFIRMAR CHECK-IN 💪", use_container_width=True):
            if nome:
                # Tenta salvar na planilha
                if salvar_agendamento(data_str, hora, nome):
                    msg = f"Olá! Sou o aluno *{nome}* e fiz check-in para o treino no dia *{data_selecionada.strftime('%d/%m')}* às *{hora}*."
                    link_wa = f"https://wa.me/{SEU_WHATSAPP}?text={urllib.parse.quote(msg)}"
                    
                    st.balloons()
                    st.success("Horário reservado com sucesso!")
                    
                    # Botão do WhatsApp (verde e chamativo)
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
