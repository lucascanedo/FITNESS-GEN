import streamlit as st
import requests

st.title("Fitness Gen – Gerador de Treino")

# Formulário de avaliação do aluno
with st.form("assessment_form"):
    name = st.text_input("Nome do aluno")
    age = st.number_input("Idade", min_value=5, max_value=100, value=25)
    sex = st.selectbox("Sexo", ["M", "F"])
    weight = st.number_input("Peso (kg)", min_value=30.0, max_value=200.0, value=70.0)
    height = st.number_input("Altura (m)", min_value=1.0, max_value=2.5, value=1.7)
    posture_issues = st.text_area("Desvios posturais (separe por vírgula)")
    injuries = st.text_area("Lesões (separe por vírgula)")
    training_history = st.text_area("Histórico de treino")
    goals = st.text_area("Objetivos (separe por vírgula)")

    submitted = st.form_submit_button("Gerar Plano")

if submitted:
    # Monta o payload
    payload = {
        "name": name,
        "age": age,
        "sex": sex,
        "weight": weight,
        "height": height,
        "posture_issues": [x.strip() for x in posture_issues.split(",") if x],
        "injuries": [x.strip() for x in injuries.split(",") if x],
        "training_history": training_history,
        "goals": [x.strip() for x in goals.split(",") if x]
    }

    # Chama o endpoint da API
    response = requests.post("http://127.0.0.1:8000/generate-plan", json=payload)

    if response.status_code == 200:
        st.success("Plano de treino gerado com sucesso!")
        plan = response.json()
        for exercise in plan:
            st.subheader(exercise["exercise"])
            st.write(f"Séries: {exercise['sets']}, Repetições: {exercise['reps']}")
            st.write(f"Foco: {exercise['focus']}")
            st.write(f"Explicação: {exercise['explanation']}")
            st.markdown("---")
    else:
        st.error(f"Erro ao gerar plano: {response.status_code}")
