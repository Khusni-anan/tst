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
        background-color: #e8f5e9;
        padding: 12px;
        border-left: 6px solid #2e7d32;
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

# --- FUNGSI PDF GENERATOR ---
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
            self.set_fill_color(232, 245, 233) 
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

    # Helper untuk label baris di PDF
    row_labels = ['A0 (Optimum)']
    # Loop manual untuk menghindari syntax error list comprehension
    for i in range(len(data_input)):
        row_labels.append(f"A{i+1}")

    # 2. Langkah 1
    pdf.chapter_title("2. Langkah 1: Matriks Keputusan & Optimal (A0)")
    df_p1 = df_s1.copy()
    if len(df_p1) == len(row_labels):
        df_p1.insert(0, 'Alt', row_labels)
    pdf.simple_table(df_p1)

    # 3. Langkah 2
    pdf.chapter_title("3. Langkah 2: Normalisasi (R)")
    df_p2 = df_s2.copy()
    if len(df_p2) == len(row_labels):
        df_p2.insert(0, 'Alt', row_labels)
    pdf.simple_table(df_p2)

    # 4. Langkah 3
    pdf.chapter_title("4. Langkah 3: Terbobot (D) & Si")
    df_p3 = df_s3.copy()
    if len(df_p3) == len(row_labels):
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

# --- SIDEBAR: KONFIGURASI BOBOT ---
st.sidebar.header("⚙️ Edit Bobot Kriteria")
w_Price = st.sidebar.slider("Price (Cost)", 0.0, 0.5, 0.30, 0.05)
w_RAM = st.sidebar.slider("RAM (Benefit)", 0.0, 0.5, 0.15, 0.05)
w_ROM = st.sidebar.slider("ROM (Benefit)", 0.0, 0.5, 0.15, 0.05)
w_Batt = st.sidebar.slider("Battery (Benefit)", 0.0, 0.5, 0.15, 0.05)
w_Cam = st.sidebar.slider("Camera (Benefit)", 0.0, 0.5, 0.25, 0.05)

bobot_list = [w_Price, w_RAM, w_ROM, w_Batt, w_Cam]
bobot_dict = {"Price": w_Price, "RAM": w_RAM, "ROM": w_ROM, "Battery": w_Batt, "Camera": w_Cam}
st.sidebar.markdown(f"**Total Bobot: {sum(bobot_list):.2f}**")

# --- DATA SMARTPHONE ---
st.title("📱 SPK Smartphone - Metode ARAS")
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
    
    alts = edited_df['Alternative'].values
    matrix = edited_df.drop('Alternative', axis=1)
    cols = matrix.columns
    types = ['cost', 'benefit', 'benefit', 'benefit', 'benefit']
    
    # 1. Menentukan X0
    x0 = []
    for i, col in enumerate(cols):
        if types[i] == 'benefit':
            x0.append(matrix[col].max())
        else:
            x0.append(matrix[col].min())
            
    df_calc = matrix.copy()
    df_x0 = pd.DataFrame([x0], columns=cols)
    df_step1 = pd.concat([df_x0, df_calc], ignore_index=True)

    # 2. Normalisasi
    df_step2 = df_step1.copy().astype(float)
    for i, col in enumerate(cols):
        if types[i] == 'benefit':
            df_step2[col] = df_step1[col] / df_step1[col].sum()
        else:
            reciprocal = 1 / df_step1[col]
            df_step2[col] = reciprocal / reciprocal.sum()

    # 3. Pembobotan & Si
    df_step3 = df_step2.copy()
    for i, col in enumerate(cols):
        df_step3[col] = df_step2[col] * bobot_list[i]
    
    Si = df_step3.sum(axis=1)
    df_step3['Total (Si)'] = Si

    # 4. Utilitas (Ki)
    S0 = Si[0]
    Ki = Si / S0

    # 5. Final Ranking
    res = pd.DataFrame({
        'Alternatif': ['OPTIMAL (A0)'] + list(alts),
        'Nilai Si (Total)': Si,
        'Nilai Ki (Utilitas)': Ki
    })
    rank_df = res.iloc[1:].copy().sort_values(by='Nilai Ki (Utilitas)', ascending=False).reset_index(drop=True)
    best = rank_df.iloc[0]

    # --- DISPLAY OUTPUT (Fixed Syntax) ---

    # Setup Label Index (Perbaikan: Tidak pakai One-Liner kompleks)
    labels_step1 = ['A0 (Optimum)']
    for i in range(len(alts)):
        labels_step1.append(f"A{i+1}")

    # LANGKAH 1
    st.markdown('<div class="step-header">LANGKAH 1: Matriks Keputusan & Nilai Optimal ($A_0$)</div>', unsafe_allow_html=True)
    df_disp_1 = df_step1.copy()
    df_disp_1.index = labels_step1
    st.dataframe(df_disp_1, use_container_width=True)

    # LANGKAH 2
    st.markdown('<div class="step-header">LANGKAH 2: Matriks Normalisasi ($R$)</div>', unsafe_allow_html=True)
    df_disp_2 = df_step2.copy()
    df_disp_2.index = labels_step1
    st.dataframe(df_disp_2.style.format("{:.4f}"), use_container_width=True)

    # LANGKAH 3
    st.markdown('<div class="step-header">LANGKAH 3: Matriks Terbobot ($D$) & Nilai Fungsi Optimalitas ($S_i$)</div>', unsafe_allow_html=True)
    labels_step3 = ['S0']
    for i in range(len(alts)):
        labels_step3.append(f"S{i+1}")
        
    df_disp_3 = df_step3.copy()
    df_disp_3.index = labels_step3
    st.dataframe(df_disp_3.style.format("{:.4f}"), use_container_width=True)

    # LANGKAH 4
    st.markdown('<div class="step-header">LANGKAH 4: Derajat Utilitas ($K_i$) & Perangkingan</div>', unsafe_allow_html=True)
    col_res, col_chart = st.columns([1, 1])
    with col_res:
        st.info(f"Nilai Optimalitas Pembanding ($S_0$) = **{S0:.4f}**")
        st.dataframe(rank_df.style.format({'Nilai Si (Total)': '{:.4f}', 'Nilai Ki (Utilitas)': '{:.4f}'}), use_container_width=True)
    with col_chart:
        st.bar_chart(rank_df.set_index('Alternatif')['Nilai Ki (Utilitas)'])

    st.success(f"🏆 Rekomendasi Terbaik: **{best['Alternatif']}** dengan skor **{best['Nilai Ki (Utilitas)']:.4f}**")

    # DOWNLOAD PDF
    st.markdown("---")
    pdf_bytes = create_dynamic_pdf(edited_df, bobot_dict, df_step1, df_step2, df_step3, rank_df, 
                                   {"nama": best['Alternatif'], "skor": best['Nilai Ki (Utilitas)']})
    
    st.download_button(
        label="📄 Download Laporan Langkah Perhitungan (PDF)",
        data=pdf_bytes,
        file_name="Laporan_ARAS_Dinamis.pdf",
        mime="application/pdf"
    )
