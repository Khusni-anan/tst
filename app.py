import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from fpdf import FPDF
from datetime import datetime

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="SPK ARAS - Locked Weights", page_icon="📱", layout="wide")

# --- CSS TAMPILAN ---
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
    }
    /* Style untuk error box */
    .stAlert {
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# --- FUNGSI PDF GENERATOR ---
def create_dynamic_pdf(data_input, bobot_dict, df_s1, df_s2, df_s3, df_rank, best_hp):
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 14)
            self.cell(0, 10, 'Laporan SPK Metode ARAS', 0, 1, 'C')
            self.set_font('Arial', 'I', 8)
            self.cell(0, 5, f'Dicetak: {datetime.now().strftime("%d-%m-%Y %H:%M")}', 0, 1, 'C')
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
    
    # 1. Data Input
    pdf.add_page()
    pdf.chapter_title("1. Data Input & Bobot")
    pdf.simple_table(data_input, [40, 30, 30, 30, 30, 30])
    w_str = ", ".join([f"{k}={v}" for k,v in bobot_dict.items()])
    pdf.multi_cell(0, 5, f"Bobot: {w_str}")
    pdf.ln(5)

    alts_list = data_input['Alternative'].tolist()
    labels_A_names = ['A0 (Optimum)'] + [f"A{i+1} ({n})" for i, n in enumerate(alts_list)]
    labels_A_short = ['A0'] + [f"A{i+1}" for i in range(len(alts_list))]
    labels_S = ['S0'] + [f"S{i+1}" for i in range(len(alts_list))]

    # 2. Langkah 1
    pdf.chapter_title("2. Langkah 1: Matriks Keputusan")
    df_p1 = df_s1.copy()
    if len(df_p1) == len(labels_A_names):
        df_p1.insert(0, 'Alt', labels_A_names) 
    pdf.simple_table(df_p1)

    # 3. Langkah 2
    pdf.chapter_title("3. Langkah 2: Normalisasi (R)")
    df_p2 = df_s2.copy()
    if len(df_p2) == len(labels_A_short):
        df_p2.insert(0, 'Alt', labels_A_short) 
    pdf.simple_table(df_p2)

    # 4. Langkah 3
    pdf.chapter_title("4. Langkah 3: Matriks Terbobot (S)")
    df_p3 = df_s3.copy()
    if len(df_p3) == len(labels_S):
        df_p3.insert(0, 'Alt', labels_S)
    pdf.simple_table(df_p3)

    # 5. Hasil
    pdf.add_page()
    pdf.chapter_title("5. Hasil Akhir & Perangkingan")
    df_rank_p = df_rank.copy()
    df_rank_p.insert(0, 'Rank', range(1, len(df_rank_p)+1))
    
    pdf.simple_table(df_rank_p[['Rank', 'Kode', 'Alternatif', 'Nilai Ki (Utilitas)']], [15, 20, 60, 35])
    
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f"Rekomendasi Terbaik: {best_hp['nama']} )", 0, 1)

    return pdf.output(dest='S').encode('latin-1')

# --- SIDEBAR: KONFIGURASI BOBOT ---
st.sidebar.header("⚙️ Edit Bobot")

# Slider Bobot
w_Price = st.sidebar.slider("Price (Cost)", 0.0, 1.0, 0.30, 0.05)
w_RAM = st.sidebar.slider("RAM (Benefit)", 0.0, 1.0, 0.15, 0.05)
w_ROM = st.sidebar.slider("ROM (Benefit)", 0.0, 1.0, 0.15, 0.05)
w_Batt = st.sidebar.slider("Battery (Benefit)", 0.0, 1.0, 0.15, 0.05)
w_Cam = st.sidebar.slider("Camera (Benefit)", 0.0, 1.0, 0.25, 0.05)

bobot_list = [w_Price, w_RAM, w_ROM, w_Batt, w_Cam]
bobot_dict = {"Price": w_Price, "RAM": w_RAM, "ROM": w_ROM, "Battery": w_Batt, "Camera": w_Cam}
total_bobot = round(sum(bobot_list), 2) # Rounding untuk menghindari float error 0.99999

st.sidebar.markdown("---")
st.sidebar.write(f"**Total Bobot Saat Ini:** {total_bobot}")

# --- LOGIKA VALIDASI BOBOT ---
is_overload = False
if total_bobot > 1.0:
    st.sidebar.error(f"❌ ERROR: Total bobot {total_bobot} melebihi 1.0!")
    st.sidebar.warning("Harap kurangi nilai bobot.")
    is_overload = True
elif total_bobot < 1.0:
    st.sidebar.warning(f"⚠️ PERINGATAN: Total bobot {total_bobot} kurang dari 1.0. (Program tetap jalan, tapi disarankan pas 1.0)")
else:
    st.sidebar.success("✅ OKE: Total bobot pas 1.0")

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

# --- TOMBOL UTAMA DENGAN VALIDASI ---
if is_overload:
    st.error("⛔ SISTEM TERKUNCI: Total bobot melebihi 1.0. Silakan perbaiki bobot di sidebar untuk melanjutkan.")
    # Tombol dibuat disabled (mati) jika overload
    st.button("🚀 Hitung & Tampilkan", type="primary", disabled=True)
else:
    # Program Normal jika bobot <= 1.0
    if st.button("🚀 Hitung & Tampilkan", type="primary"):
        
        # --- CORE CALCULATION ---
        alts = edited_df['Alternative'].values
        matrix = edited_df.drop('Alternative', axis=1)
        cols = matrix.columns
        types = ['cost', 'benefit', 'benefit', 'benefit', 'benefit']
        
        # 1. X0
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

        # 3. Pembobotan
        df_step3 = df_step2.copy()
        for i, col in enumerate(cols):
            df_step3[col] = df_step2[col] * bobot_list[i]
        
        Si = df_step3.sum(axis=1)
        df_step3['Total (Si)'] = Si

        # 4. Utilitas
        S0 = Si[0]
        Ki = Si / S0

        # 5. Hasil
        kode_awal = ['A0'] + [f"A{i+1}" for i in range(len(alts))]
        res = pd.DataFrame({
            'Kode': kode_awal,
            'Alternatif': ['OPTIMAL (A0)'] + list(alts),
            'Nilai Si (Total)': Si,
            'Nilai Ki (Utilitas)': Ki
        })
        
        # Split Data untuk Ranking & Grafik
        rank_df = res.iloc[1:].copy().sort_values(by='Nilai Ki (Utilitas)', ascending=False).reset_index(drop=True)
        best = rank_df.iloc[0]
        chart_df = res.iloc[1:].copy() 
        
        # --- DISPLAY ---
        labels_step1 = ['A0 (Optimum)'] + [f"A{i+1} ({n})" for i, n in enumerate(alts)]
        labels_step2 = ['A0'] + [f"A{i+1}" for i in range(len(alts))] 
        labels_step3 = ['S0'] + [f"S{i+1}" for i in range(len(alts))] 

        st.markdown('<div class="step-header">LANGKAH 1: Matriks Keputusan (A)</div>', unsafe_allow_html=True)
        df_disp_1 = df_step1.copy()
        df_disp_1.index = labels_step1 
        st.dataframe(df_disp_1, use_container_width=True)

        st.markdown('<div class="step-header">LANGKAH 2: Normalisasi (R)</div>', unsafe_allow_html=True)
        df_disp_2 = df_step2.copy()
        df_disp_2.index = labels_step2
        st.dataframe(df_disp_2.style.format("{:.4f}"), use_container_width=True)

        st.markdown('<div class="step-header">LANGKAH 3: Matriks Terbobot (S)</div>', unsafe_allow_html=True)
        df_disp_3 = df_step3.copy()
        df_disp_3.index = labels_step3 
        st.dataframe(df_disp_3.style.format("{:.4f}"), use_container_width=True)

        st.markdown('<div class="step-header">HASIL PERANGKINGAN</div>', unsafe_allow_html=True)
        st.info(f"Nilai Optimalitas (S0) = **{S0:.4f}**")
        
        col_res, col_chart = st.columns([1.2, 1])
        
        with col_res:
            st.write("Tabel Peringkat (Urut Skor Tertinggi):")
            st.dataframe(
                rank_df[['Kode', 'Alternatif', 'Nilai Si (Total)', 'Nilai Ki (Utilitas)']]
                .style.format({'Nilai Si (Total)': '{:.4f}', 'Nilai Ki (Utilitas)': '{:.4f}'}),
                use_container_width=True
            )
        
        with col_chart:
            st.write("Grafik Utilitas (Sesuai Urutan Input):")
            c = alt.Chart(chart_df).mark_bar().encode(
                x=alt.X('Alternatif', sort=None),
                y='Nilai Ki (Utilitas)',
                tooltip=['Alternatif', 'Nilai Ki (Utilitas)']
            ).interactive()
            st.altair_chart(c, use_container_width=True)
        
        st.success(f"🏆 Juara 1: **{best['Alternatif']}** ")

        st.markdown("---")
        pdf_bytes = create_dynamic_pdf(edited_df, bobot_dict, df_step1, df_step2, df_step3, rank_df, 
                                       {"nama": best['Alternatif'], "kode": best['Kode']})
        
        st.download_button(
            label="📄 Download Laporan Lengkap (PDF)",
            data=pdf_bytes,
            file_name="Laporan_ARAS_Final.pdf",
            mime="application/pdf"
        )
