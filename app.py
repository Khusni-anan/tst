import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
from datetime import datetime

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="SPK ARAS - Dynamic", page_icon="📱", layout="wide")

# --- CSS TAMPILAN (Gaya Slide) ---
st.markdown("""
    <style>
    .step-header {
        background-color: #e8f5e9; /* Hijau muda halus */
        padding: 12px;
        border-left: 6px solid #2e7d32; /* Hijau tua */
        margin-top: 25px;
        margin-bottom: 15px;
        font-weight: bold;
        font-size: 18px;
        color: #1b5e20;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .info-box {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #dee2e6;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- FUNGSI PDF GENERATOR (Dinamis) ---
def create_dynamic_pdf(data_input, bobot_dict, df_s1, df_s2, df_s3, df_rank, best_hp):
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 14)
            self.cell(0, 10, 'Laporan Detail Perhitungan SPK ARAS', 0, 1, 'C')
            self.set_font('Arial', 'I', 8)
            self.cell(0, 5, f'Tanggal Cetak: {datetime.now().strftime("%d-%m-%Y %H:%M")}', 0, 1, 'C')
            self.line(10, 25, 200, 25)
            self.ln(10)
        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Halaman {self.page_no()}', 0, 0, 'C')
        def chapter_title(self, title):
            self.set_fill_color(232, 245, 233) # Hijau muda background
            self.set_font('Arial', 'B', 11)
            self.cell(0, 8, title, 0, 1, 'L', 1)
            self.ln(2)
        def simple_table(self, df, col_widths=None):
            self.set_font('Arial', 'B', 8)
            cols = df.columns
            if not col_widths: col_widths = [190 / len(cols)] * len(cols)
            for i, col in enumerate(cols):
                self.cell(col_widths[i], 6, str(col), 1, 0, 'C')
            self.ln()
            self.set_font('Arial', '', 8)
            for _, row in df.iterrows():
                for i, col in enumerate(cols):
                    val = row[col]
                    if isinstance(val, (float, np.floating)):
                        val = f"{val:.4f}" if val != int(val) else f"{int(val)}"
                    self.cell(col_widths[i], 6, str(val), 1, 0, 'C')
                self.ln()
            self.ln(4)

    pdf = PDF()
    
    # 1. Input Data
    pdf.add_page()
    pdf.chapter_title("1. Data Input & Bobot")
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 5, "Data Smartphone yang dianalisis:")
    pdf.simple_table(data_input, [40, 30, 30, 30, 30, 30])
    
    pdf.multi_cell(0, 5, "Bobot Kriteria:")
    w_text = ", ".join([f"{k}={v}" for k,v in bobot_dict.items()])
    pdf.multi_cell(0, 5, w_text)
    pdf.ln(5)

    # 2. Langkah 1
    pdf.chapter_title("2. Langkah 1: Matriks Keputusan & Optimal (A0)")
    # Format tabel: Tambahkan label baris
    df_p1 = df_s1.copy()
    row_labels = ['A0 (Optimum)'] + [f"A{i+1}" for i in range(len(df_p1)-1)]
    df_p1.insert(0, 'Alt', row_labels)
    pdf.simple_table(df_p1)

    # 3. Langkah 2
    pdf.chapter_title("3. Langkah 2: Normalisasi (R)")
    df_p2 = df_s2.copy()
    df_p2.insert(0, 'Alt', row_labels)
    pdf.simple_table(df_p2)

    # 4. Langkah 3
    pdf.chapter_title("4. Langkah 3: Terbobot (D) & Si")
    df_p3 = df_s3.copy()
    df_p3.insert(0, 'Alt', row_labels)
    pdf.simple_table(df_p3)

    # 5. Hasil
    pdf.add_page()
    pdf.chapter_title("5. Hasil Akhir (Perangkingan)")
    df_rank_p = df_rank.copy()
    df_rank_p.insert(0, 'Rank', range(1, len(df_rank_p)+1))
    pdf.simple_table(df_rank_p[['Rank', 'Alternatif', 'Nilai Si (Total)', 'Nilai Ki (Utilitas)']], [20, 70, 40, 40])
    
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f"Rekomendasi Terbaik: {best_hp['nama']} (Ki = {best_hp['skor']:.4f})", 0, 1)

    return pdf.output(dest='S').encode('latin-1')

# --- SIDEBAR: KONFIGURASI BOBOT (EDITABLE) ---
st.sidebar.header("⚙️ Edit Bobot Kriteria")
st.sidebar.caption("Sesuaikan bobot prioritas Anda.")

w_Price = st.sidebar.slider("Price (Cost)", 0.0, 0.5, 0.30, 0.05)
w_RAM = st.sidebar.slider("RAM (Benefit)", 0.0, 0.5, 0.15, 0.05)
w_ROM = st.sidebar.slider("ROM (Benefit)", 0.0, 0.5, 0.15, 0.05)
w_Batt = st.sidebar.slider("Battery (Benefit)", 0.0, 0.5, 0.15, 0.05)
w_Cam = st.sidebar.slider("Camera (Benefit)", 0.0, 0.5, 0.25, 0.05)

bobot_list = [w_Price, w_RAM, w_ROM, w_Batt, w_Cam]
bobot_dict = {"Price": w_Price, "RAM": w_RAM, "ROM": w_ROM, "Battery": w_Batt, "Camera": w_Cam}
total_w = sum(bobot_list)

st.sidebar.markdown(f"**Total Bobot: {total_w:.2f}**")
if not np.isclose(total_w, 1.0):
    st.sidebar.warning("⚠️ Total bobot disarankan 1.0")

# --- HALAMAN UTAMA: DATA SMARTPHONE (EDITABLE) ---
st.title("📱 SPK Smartphone - Metode ARAS")
st.write("Silakan ubah **Data Smartphone** di tabel bawah ini, lalu klik tombol Hitung.")

# Data Awal (Default seperti gambar, tapi bisa diedit)
default_data = {
    'Alternative': ['Samsung Galaxy A54', 'Xiaomi 13T', 'Infinix GT 10 Pro', 'Realme 11 Pro'],
    'Price': [5.9, 6.5, 4.4, 5.5],
    'RAM': [8, 12, 8, 12],
    'ROM': [256, 256, 256, 512],
    'Battery': [5000, 5000, 5000, 5000],
    'Camera': [50, 50, 108, 100]
}
df_input = pd.DataFrame(default_data)
edited_df = st.data_editor(df_input, num_rows="dynamic", use_container_width=True)

# --- ENGINE PERHITUNGAN ---
if st.button("🚀 Hitung & Tampilkan Langkah", type="primary"):
    
    # 1. Persiapan Data
    alts = edited_df['Alternative'].values
    matrix = edited_df.drop('Alternative', axis=1)
    cols = matrix.columns
    # Tipe kriteria (Hardcoded urutannya: Price=Cost, sisanya Benefit)
    types = ['cost', 'benefit', 'benefit', 'benefit', 'benefit'] 
    
    # 2. Menentukan X0 (Optimal)
    x0 = []
    for i
