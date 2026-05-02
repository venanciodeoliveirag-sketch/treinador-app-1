import streamlit as st
from datetime import datetime

st.set_page_config(page_title="Agenda de Personal", page_icon="💪")

# Título do App
st.title("💪 Agendamento de Personal Trainer")
st.write("Verifique minha disponibilidade e agende seu horário.")

# --- CONFIGURAÇÃO DA ESCALA ---
# Data de referência: Segunda-feira (27/04/2026), início da sua 'semana cheia'
DATA_REFERENCIA = datetime(2026, 4, 27).date()
# Coloque seu número com 55 + DDD + Numero (tudo junto)
SEU_WHATSAPP = "+55 28 999896258" 

def verificar_disponibilidade(data):
    # Regra do Domingo (Folga fixa)
    if data.weekday() == 6:
        return "Domingo - Folga Fixa", False
    
    # Cálculo da escala 2x2 (Trabalha 2, Folga 2)
    delta_dias = (data - DATA_REFERENCIA).days
    posicao = delta_dias % 4
    
    if posicao in [0, 1]:
        return "Plantão PM (Indisponível)", False
    else:
        return "Disponível para Personal", True

# --- INTERFACE ---
data_selecionada = st.date_input("Selecione a data da aula:", min_value=datetime.today())
status, disponivel = verificar_disponibilidade(data_selecionada)

if not disponivel:
    st.error(f"🚫 {status}")
    st.info("Por favor, escolha outro dia no calendário.")
else:
    st.success(f"✅ {status}")
    horarios = ["06:00", "07:00", "08:00", "09:00", "19:00", "20:00", "21:00"]
    hora = st.selectbox("Escolha o horário disponível:", horarios)
    nome = st.text_input("Seu nome completo:")
    
    if st.button("Confirmar Check-in"):
        if nome:
            msg = f"Olá! Sou o aluno {nome} e fiz check-in para o dia {data_selecionada.strftime('%d/%m')} às {hora}."
            link = f"https://wa.me/{SEU_WHATSAPP}?text={msg.replace(' ', '%20')}"
            st.balloons()
            st.markdown(f'''
                <a href="{link}" target="_blank">
                    <button style="width:100%;height:50px;border-radius:10px;background-color:#25d366;color:white;border:none;font-weight:bold;cursor:pointer;">
                        NOTIFICAR PERSONAL NO WHATSAPP
                    </button>
                </a>
            ''', unsafe_allow_html=True)
        else:
            st.warning("Por favor, digite seu nome.")
