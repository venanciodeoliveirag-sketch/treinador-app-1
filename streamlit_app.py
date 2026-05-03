import streamlit as st
from datetime import datetime, timedelta
import urllib.parse
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Agenda de Personal", page_icon="💪")

# --- CONEXÃO COM GOOGLE SHEETS ---
# Utiliza as credenciais configuradas nos Secrets do Streamlit
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

# --- TÍTULO ---
st.title("💪 Agendamento de Personal Trainer")
st.write("Verifique minha disponibilidade e agende seu horário.")

# ==================================================
# --- VITRINE DA SEMANA (LAYOUT PARA CELULAR) ---
# ==================================================
st.write("### 📅 Previsão dos próximos 7 dias:")

# HTML/CSS para forçar os itens a ficarem na horizontal no celular
html_vitrine = "<div style='display: flex; justify-content: space-between; padding: 10px; border-radius: 10px; overflow-x: auto;'>"
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
            <span style='font-size: 24px;'>{icone}</span>
        </div>
    """

html_vitrine += "</div>"
st.markdown(html_vitrine, unsafe_allow_html=True)
st.divider()

# --- INTERFACE DE AGENDAMENTO ---
data_selecionada = st.date_input("Selecione a data da aula no calendário abaixo:", min_value=datetime.today())
status_dia, disponivel_dia = verificar_disponibilidade(data_selecionada)

if not disponivel_dia:
    st.error(f"🚫 {status_dia}")
else:
    st.success(f"✅ {status_dia}")
    
    # Carregar agendamentos já feitos
    try:
        df_agendamentos = carregar_dados()
        data_str = data_selecionada.strftime("%Y-%m-%d")
        
        if not df_agendamentos.empty and "Data" in df_agendamentos.columns and "Hora" in df_agendamentos.columns:
            ocupados = df_agendamentos[df_agendamentos["Data"] == data_str]["Hora"].tolist()
        else:
            ocupados = []
            
        horarios_padrao = ["06:00", "07:00", "08:00", "09:00", "19:00", "20:00", "21:00"]
        horarios_livres = [h for h in horarios_padrao if h not in ocupados]
        
        if not horarios_livres:
            st.warning("Poxa, todos os horários para este dia já foram preenchidos!")
        else:
            hora = st.selectbox("Escolha o horário disponível:", horarios_livres)
            nome = st.text_input("Seu nome completo:")

            if st.button("Confirmar Check-in"):
                if nome:
                    # Tenta salvar na planilha
                    if salvar_agendamento(data_str, hora, nome):
                        msg = f"Olá! Sou o aluno {nome} e fiz check-in para o dia {data_selecionada.strftime('%d/%m')} às {hora}."
                        link_wa = f"https://wa.me/{SEU_WHATSAPP}?text={urllib.parse.quote(msg)}"
                        
                        st.balloons()
                        st.success("Horário reservado na planilha com sucesso!")
                        st.markdown(f'''
                            <a href="{link_wa}" target="_blank">
                                <button style="width:100%;height:50px;border-radius:10px;background-color:#25d366;color:white;border:none;font-weight:bold;cursor:pointer;">
                                    NOTIFICAR PERSONAL NO WHATSAPP
                                </button>
                            </a>
                        ''', unsafe_allow_html=True)
                        st.cache_data.clear() # Limpa o cache para atualizar a lista de horários
                    else:
                        st.error("Erro: Este horário acabou de ser preenchido por outra pessoa.")
                else:
                    st.warning("Por favor, digite seu nome.")
    except Exception as e:
        st.error("Erro ao conectar com a planilha. Verifique os Secrets.")
