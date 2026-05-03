import streamlit as st
from datetime import datetime, timedelta # Adicionado timedelta aqui
import urllib.parse
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Agenda de Personal", page_icon="💪")

# --- CONEXÃO COM GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    return conn.read(ttl=0, usecols=[0, 1, 2]).dropna(how="all")

def salvar_agendamento(data_str, hora, nome):
    df_existente = carregar_dados()
    conflito = df_existente[(df_existente["Data"] == data_str) & (df_existente["Hora"] == hora)]
    
    if conflito.empty:
        novo_registro = pd.DataFrame([{"Data": data_str, "Hora": hora, "Nome": nome}])
        df_atualizado = pd.concat([df_existente, novo_registro], ignore_index=True)
        # Atenção: O nome da conexão nos secrets deve estar apontando para a sua planilha
        conn.update(data=df_atualizado) 
        return True
    return False

# --- CONFIGURAÇÃO DA ESCALA ---
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

# --- TÍTULO DO APP ---
st.title("💪 Agendamento de Personal Trainer")
st.write("Verifique minha disponibilidade e agende seu horário.")


# ==========================================
# --- VITRINE DA SEMANA (CÓDIGO NOVO AQUI) ---
# ==========================================
st.write("### 📅 Previsão dos próximos 7 dias:")

colunas_dias = st.columns(7)
hoje = datetime.today().date()

for i in range(7):
    dia_previsao = hoje + timedelta(days=i)
    status_prev, disponivel_prev = verificar_disponibilidade(dia_previsao)
    dia_semana = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"][dia_previsao.weekday()]
    
    with colunas_dias[i]:
        st.markdown(f"<div style='text-align: center; font-size: 14px;'><b>{dia_semana}</b><br>{dia_previsao.strftime('%d/%m')}</div>", unsafe_allow_html=True)
        
        if not disponivel_prev:
            if dia_previsao.weekday() == 6:
                st.markdown("<div style='text-align: center; font-size: 24px;'>🏖️</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='text-align: center; font-size: 24px;'>🚔</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='text-align: center; font-size: 24px;'>✅</div>", unsafe_allow_html=True)

st.divider() 
# ==========================================


# --- INTERFACE (Escolha de Data) ---
data_selecionada = st.date_input("Selecione a data da aula no calendário abaixo:", min_value=datetime.today())
status, disponivel = verificar_disponibilidade(data_selecionada)

if not disponivel:
    st.error(f"🚫 {status}")
else:
    st.success(f"✅ {status}")
    
    # Carregar agendamentos
    df_agendamentos = carregar_dados()
    data_str = data_selecionada.strftime("%Y-%m-%d")
    
    # Filtrar horários ocupados
    if not df_agendamentos.empty and "Data" in df_agendamentos.columns and "Hora" in df_agendamentos.columns:
        ocupados = df_agendamentos[df_agendamentos["Data"] == data_str]["Hora"].tolist()
    else:
        ocupados = []
    
    horarios_padrao = ["06:00", "07:00", "08:00", "09:00", "19:00", "20:00", "21:00"]
    horarios_livres = [h for h in horarios_padrao if h not in ocupados]
    
    if not horarios_livres:
        st.warning("Todos os horários estão ocupados para este dia.")
    else:
        hora = st.selectbox("Escolha o horário:", horarios_livres)
        nome = st.text_input("Seu nome completo:")

        if st.button("Confirmar Check-in"):
            if nome:
                if salvar_agendamento(data_str, hora, nome):
                    msg = f"Olá! Sou o aluno {nome} e fiz check-in para o dia {data_selecionada.strftime('%d/%m')} às {hora}."
                    link = f"https://wa.me/{SEU_WHATSAPP}?text={urllib.parse.quote(msg)}"
                    
                    st.balloons()
                    st.success("Agendamento guardado com sucesso!")
                    st.markdown(f'''
                        <a href="{link}" target="_blank">
                            <button style="width:100%;height:50px;border-radius:10px;background-color:#25d366;color:white;border:none;font-weight:bold;cursor:pointer;">
                                NOTIFICAR PERSONAL NO WHATSAPP
                            </button>
                        </a>
                    ''', unsafe_allow_html=True)
                    st.cache_data.clear()
                else:
                    st.error("Erro: Este horário foi preenchido por outra pessoa agora mesmo.")
            else:
                st.warning("Introduza o seu nome.")
