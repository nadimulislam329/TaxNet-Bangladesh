import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import os

# Page configuration
st.set_page_config(
    page_title="QA Review Interface", 
    page_icon="🧠", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS styling
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    * { font-family: 'Inter', sans-serif; }
    .main { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
    
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        background-size: 200% 200%;
        animation: gradientShift 8s ease infinite;
        padding: 2.5rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        color: white;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    .question-card {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
        padding: 2rem;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.3);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        margin: 1.5rem 0;
        transition: transform 0.3s ease;
    }
    
    .question-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
    }
    
    .stTextArea textarea {
        border: 2px solid #e0e7ff !important;
        border-radius: 10px !important;
        padding: 15px !important;
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%) !important;
    }
    
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(255, 255, 255, 0.9);
        padding: 1rem;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 60px;
        background: white;
        border-radius: 10px;
        font-weight: 600;
        padding: 0 2rem;
        border: 2px solid #e0e7ff;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
    <div class="main-header">
        <h1>🧠 QA Review Interface</h1>
        <p style='font-size: 1.1rem; margin: 0;'>✨ Evaluate model responses by category</p>
    </div>
""", unsafe_allow_html=True)

# Timezone
bd_tz = pytz.timezone('Asia/Dhaka')

# File paths
OUTPUT_FILE = "qa_dataset_with_remarks.csv"
INPUT_FILE = "TaxNet.csv"

# Load data
@st.cache_data
def load_data():
    try:
        df = pd.read_csv(INPUT_FILE)
        required_cols = ['Question', 'Answer', 'Gold Answer', 'Category']
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            st.error(f"❌ Missing columns: {', '.join(missing)}")
            st.stop()
        return df
    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        st.stop()

df = load_data()

def load_existing_reviews():
    if os.path.exists(OUTPUT_FILE):
        try:
            return pd.read_csv(OUTPUT_FILE)
        except:
            return None
    return None

# Sidebar
with st.sidebar:
    st.markdown("### 📋 Review Settings")
    reviewer_name = st.text_input("👤 Reviewer Name:", placeholder="Enter your name")
    
    current_time = datetime.now(bd_tz).strftime("%Y-%m-%d %I:%M:%S %p")
    st.info(f"📅 {current_time}")
    
    st.markdown("---")
    st.markdown("### 📖 Instructions")
    st.markdown("""
    1. Select a category tab
    2. Read the question
    3. Compare answers
    4. Rate & add remarks
    5. Navigate with buttons
    6. Auto-saves!
    """)
    
    st.markdown("---")
    if os.path.exists(OUTPUT_FILE):
        df_download = pd.read_csv(OUTPUT_FILE)
        csv = df_download.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Download CSV",
            data=csv,
            file_name=f"reviews_{datetime.now(bd_tz).strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )

# Initialize session state
categories = ['Tax Payer', 'Non-Tax Payer', 'Income Tax Officer']
for category in categories:
    if f"index_{category}" not in st.session_state:
        st.session_state[f"index_{category}"] = 0
    if f"remark_counter_{category}" not in st.session_state:
        st.session_state[f"remark_counter_{category}"] = 0
    if f"rating_counter_{category}" not in st.session_state:
        st.session_state[f"rating_counter_{category}"] = 0

# Create tabs
tab1, tab2, tab3 = st.tabs(["👤 Tax Payer", "🏢 Non-Tax Payer", "👔 Income Tax Officer"])

def render_category_content(category, tab):
    with tab:
        category_df = df[df['Category'] == category].reset_index(drop=True)
        
        if len(category_df) == 0:
            st.warning(f"⚠️ No questions for: {category}")
            return
        
        current_idx = st.session_state[f"index_{category}"]
        progress = (current_idx + 1) / len(category_df)
        st.progress(progress)
        st.caption(f"📊 Question {current_idx + 1} of {len(category_df)}")
        
        row = category_df.iloc[current_idx]
        
        # Load existing review
        existing_rating = None
        existing_remark = ""
        df_saved = load_existing_reviews()
        
        if df_saved is not None:
            matching = df_saved[df_saved['Question'] == row['Question']]
            if len(matching) > 0:
                saved = matching.iloc[0]
                if 'Rating' in saved and pd.notna(saved['Rating']):
                    existing_rating = saved['Rating']
                if 'Remarks' in saved and pd.notna(saved['Remarks']):
                    existing_remark = saved['Remarks']
        
        # Display question
        st.markdown(f"""
            <div class="question-card">
                <p><strong>❓ Question:</strong></p>
                <p style="margin-top: 0.8rem; font-size: 1.05rem;">{row['Question']}</p>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 🤖 Model Answer")
            st.info(row['Answer'])
        with col2:
            st.markdown("#### ✅ Gold Answer")
            st.success(row['Gold Answer'])
        
        # Rating
        st.markdown("---")
        st.markdown("### ⭐ Rate the Answer")
        
        rating_options = {
            "⭐⭐⭐⭐⭐ Excellent": 5,
            "⭐⭐⭐⭐ Good": 4,
            "⭐⭐⭐ Fair": 3,
            "⭐⭐ Poor": 2,
            "⭐ Very Poor": 1
        }
        
        default_idx = None
        if existing_rating and existing_rating in rating_options:
            default_idx = list(rating_options.keys()).index(existing_rating)
        
        rating = st.radio(
            "Select rating:",
            options=list(rating_options.keys()),
            index=default_idx,
            key=f"rating_{category}_{current_idx}_{st.session_state[f'rating_counter_{category}']}",
            horizontal=True
        )
        
        # Remarks
        st.markdown("---")
        remark = st.text_area(
            "💭 Your Remarks:",
            value=existing_remark,
            height=150,
            key=f"remark_{category}_{current_idx}_{st.session_state[f'remark_counter_{category}']}",
            placeholder="Write your observations..."
        )
        
        def save_review():
            if rating or remark.strip():
                try:
                    if os.path.exists(OUTPUT_FILE):
                        df_saved = pd.read_csv(OUTPUT_FILE)
                    else:
                        df_saved = df.copy()
                        for col in ['Rating', 'Rating_Value', 'Remarks', 'Reviewer', 'Review_Date']:
                            df_saved[col] = ""
                    
                    mask = df_saved['Question'] == row['Question']
                    if mask.any():
                        idx = df_saved[mask].index[0]
                        if rating:
                            df_saved.at[idx, 'Rating'] = rating
                            df_saved.at[idx, 'Rating_Value'] = rating_options[rating]
                        if remark.strip():
                            df_saved.at[idx, 'Remarks'] = remark
                        df_saved.at[idx, 'Reviewer'] = reviewer_name or "Anonymous"
                        df_saved.at[idx, 'Review_Date'] = datetime.now(bd_tz).strftime("%Y-%m-%d %I:%M:%S %p")
                        
                        df_saved.to_csv(OUTPUT_FILE, index=False)
                        return True
                except Exception as e:
                    st.error(f"Save error: {e}")
            return False
        
        def navigate(direction):
            save_review()
            st.session_state[f"remark_counter_{category}"] += 1
            st.session_state[f"rating_counter_{category}"] += 1
            
            if direction == "prev":
                st.session_state[f"index_{category}"] = max(0, current_idx - 1)
            else:
                st.session_state[f"index_{category}"] = min(len(category_df) - 1, current_idx + 1)
        
        # Navigation buttons
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("⬅️ Previous", use_container_width=True, disabled=(current_idx==0), key=f"prev_{category}"):
                navigate("prev")
                st.rerun()
        
        with col2:
            if current_idx == len(category_df) - 1:
                if st.button("💾 Save & Finish", use_container_width=True, type="primary", key=f"finish_{category}"):
                    if save_review():
                        st.success("✅ Saved!")
                        st.rerun()
            else:
                if st.button("Next ➡️", use_container_width=True, key=f"next_{category}"):
                    navigate("next")
                    st.rerun()

render_category_content('Tax Payer', tab1)
render_category_content('Non-Tax Payer', tab2)
render_category_content('Income Tax Officer', tab3)
