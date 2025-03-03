import streamlit as st
import cv2
import numpy as np
import os
import pandas as pd
from pathlib import Path
from face_analysis_main import FaceAnalysisPipeline
import openai

st.set_option('server.runOnSave', False)
# Настройка страницы
st.set_page_config(
    page_title="Анализ лиц в видео",
    page_icon="🎥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Создание необходимых директорий
def create_directories():
    try:
        Path("storage/videos").mkdir(parents=True, exist_ok=True)
        Path("storage/results").mkdir(parents=True, exist_ok=True)
    except Exception as e:
        st.error(f"Ошибка при создании директорий: {str(e)}")
        raise

# Анализ CSV данных
def analyze_csv(csv_path):
    try:
        df = pd.read_csv(csv_path)
        expression_counts = df["Expression"].value_counts()
        avg_confidence = df.groupby("Expression")["Confidence"].mean()
        
        summary = f"""
        📊 **Статистика по выражениям лиц**:
        - Количество выражений:
        {expression_counts.to_string()}
        - Средняя уверенность:
        {avg_confidence.to_string()}
        """
        
        return df, summary
    except Exception as e:
        return None, f"Ошибка при анализе CSV: {str(e)}"

# Отправка анализа в OpenAI API
def get_openai_insights(df):
    try:
        api_key = st.secrets.get("openai_api_key")
        if not api_key:
            return "Ошибка: API ключ отсутствует"
        
        client = openai.OpenAI(api_key=api_key)
        summary_prompt = f"""
        Данные анализа выражений лиц:
        {df.to_string()}
        На основе этих данных сделай краткий аналитический отчет о поведении испытуемых, динамике настроения и возможных выводах.
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты опытный аналитик по эмоциям и поведенческому анализу."},
                {"role": "user", "content": summary_prompt}
            ],
            max_tokens=500,
            temperature=0.5
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Ошибка при запросе к OpenAI API: {str(e)}"

# Запуск анализа
def run_face_analysis(video_path):
    try:
        st.info("🔍 Запуск анализа видео...")
        model_path = "./yolov8n-face.pt"
        pipeline = FaceAnalysisPipeline(model_path, video_path)
        pipeline.run_analysis()
        
        csv_path = f"storage/results/{Path(video_path).stem}.csv"
        if os.path.exists(csv_path):
            return csv_path
        else:
            return None
    except Exception as e:
        st.error(f"Ошибка при запуске анализа: {str(e)}")
        return None

# Основной контент
st.header("🎥 Анализ лиц в видео")

uploaded_file = st.file_uploader(
    "Выберите видеофайл (MP4)",
    type=["mp4"],
    help="Загрузите видеофайл в формате MP4"
)

if uploaded_file is not None:
    create_directories()
    video_path = f"storage/videos/{uploaded_file.name}"
    
    with open(video_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    st.success("Видео успешно загружено!")
    
    if st.button("Запустить анализ лиц"):
        with st.spinner("Обработка видео..."):
            csv_path = run_face_analysis(video_path)
            
            if csv_path:
                df, summary = analyze_csv(csv_path)
                if df is not None:
                    st.subheader("📊 Анализ данных")
                    st.write(summary)
                    
                    st.subheader("🧠 Инсайты от OpenAI")
                    insights = get_openai_insights(df)
                    st.write(insights)
                    
                    st.download_button(
                        label="💾 Скачать CSV файл",
                        data=df.to_csv(index=False),
                        file_name=f"{uploaded_file.name.replace('.mp4', '.csv')}",
                        mime="text/csv"
                    )
                else:
                    st.error(summary)
            else:
                st.error("CSV файл с результатами анализа не найден.")

# Нижний колонтитул
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        © 2024 Анализ лиц в видео | Версия 1.0
    </div>
    """,
    unsafe_allow_html=True 
)
