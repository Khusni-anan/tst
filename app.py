import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
from datetime import datetime

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="SPK ARAS - Step by Step", page_icon="📱", layout="wide")

# --- CSS UNTUK TAMPILAN MIRIP SLIDE ---
st.markdown("""
    <style>
    .step-header {
        background-color: #f0f2f6;
        padding: 10px;
        border-left: 5px solid #4CAF50;
        margin-top: 20px;
        margin-bottom: 10px;
        font-weight: bold;
        font-size: 20px;
    }
    .explanation {
        font-size: 16px;
        color: #333;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- FUNGSI PDF ALA SLIDE PRESENTASI ---
def create_slide_pdf(data_input, bobot_df, df_step1, df_step2, df_step3, df_ranking, best_choice):
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 14)
            self.cell(0, 10, 'Laporan Perhitungan SPK Metode ARAS', 0, 1, 'C')
            self.set_font('Arial', 'I', 8)
            self.cell(0, 5, f'Dicetak pada: {datetime.now().strftime("%d-%m-%Y %H:%M")}', 0, 1, 'C')
            self.line(10, 25, 200, 25)
            self.ln(10)

        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Halaman {self.page_no()}', 0, 0, 'C')

        def section_title(self, title):
            self.set_fill_color(230, 230, 230)
            self.set_font('Arial', 'B', 11)
            self.cell(0, 8, title, 0, 1, 'L', 1)
            self.ln(2)

        def narrative(self, text):
            self.set_font('Arial', '', 10)
            self.multi_cell(0, 5, text)
            self.ln(3)

        def simple_table(self, df, col_widths=None):
            self.set_font('Arial', 'B', 9)
            cols = df.columns
            if not col_widths:
                col_widths = [190 / len(cols)] * len(cols)
            
            # Header
            for i, col in enumerate(cols):
                self.cell(col_widths[i], 7, str(col), 1, 0, 'C')
            self.ln()
            
            # Rows
            self.set_font('Arial', '', 9)
            for index, row in df.iterrows():
                for i, col in enumerate(cols):
                    val = row[col]
                    if isinstance(val, (float, np.floating)):
                        val = f"{val:.4f}" if val != int(val) else f"{int(val)}"
                    self.cell(col_widths[i], 7, str(val), 1, 0, 'C')
                self.ln()
            self.ln(5)

    pdf = PDF()
    
    # HALAMAN 1: STUDI KASUS & KRITERIA
    pdf.add_page()
    pdf.section_title("1. Studi Kasus (Data Smartphone)")
    pdf.narrative("Berikut adalah data alternatif smartphone yang akan dianalisis:")
    # Tabel Data Awal
    cw_data = [40, 30, 30, 30, 30, 30]
    pdf.simple_table(data_input, cw_data)

    pdf.ln(5)
    pdf.section_title("2. Analisis Kriteria dan Bobot")
    pdf.narrative("Bobot dan jenis kriteria ditentukan sebagai berikut (Sesuai Gambar):")
    # Tabel Bobot
    cw_bobot = [30, 50, 40, 40] # Kode, Kriteria, Tipe, Bobot
    pdf.simple_table(bobot_df, cw_bobot)

    # HALAMAN 2: LANGKAH 1
    pdf.add_page()
    pdf.section_title("LANGKAH 1 - Matriks Keputusan & Nilai Optimum (A0)")
    pdf.narrative("Menentukan nilai Optimum (A0) berdasarkan prinsip Max untuk Benefit dan Min untuk Cost.")
    
    # Siapkan tabel Langkah 1 (tambah label A0, A1...)
    df_s1_print = df_step1.copy()
    labels = ['A0 (Optimum)'] + [f"A{i+1}" for i in range(len(df_s1_print)-1)]
    df_s1_print.insert(0, 'Alt', labels)
    cw_matrix = [25, 30, 30, 30, 35, 30]
    pdf.simple_table(df_s1_print, cw_matrix)
    pdf.narrative("Catatan: A0 Price diambil yang terendah (4.4) karena Cost. Sisanya diambil yang tertinggi (Benefit).")

    # HALAMAN 3: LANGKAH 2 (NORMALISASI)
    pdf.add_page()
    pdf.section_title("LANGKAH 2 - Normalisasi Matriks (R)")
    pdf.narrative("Perhitungan khusus untuk C1 (Price) karena bertipe Cost (1/x), kemudian dibagi totalnya.")
    pdf.narrative("Hasil normalisasi lengkap untuk semua kriteria:")
    
    # Tabel Normalisasi
    df_s2_print = df_step2.copy()
    df_s2_print.insert(0, 'Alt', labels)
    pdf.simple_table(df_s2_print, cw_matrix)

    # HALAMAN 4: LANGKAH 3 (TERBOBOT)
    pdf.add_page()
    pdf.section_title("LANGKAH 3 - Matriks Terbobot (D)")
    pdf.narrative("Mengalikan nilai normalisasi dengan bobot (W). Menghasilkan nilai Si (Total Baris).")
    
    df_s3_print = df_step3.copy()
    df_s3_print.insert(0, 'Alt', labels)
    cw_weighted = [25, 25, 25, 25, 25, 25, 30] # + kolom Si
    pdf.simple_table(df_s3_print, cw_weighted)

    # HALAMAN 5: LANGKAH 4 & 5 (HASIL)
    pdf.add_page()
    pdf.section_title("LANGKAH 4 & 5 - Utilitas (Ki) dan Perangkingan")
    pdf.narrative("Menghitung Derajat Utilitas Ki = Si / S0.")
    
    # Tabel Ranking
    df_rank_print = df_ranking.copy()
    df_rank_print.insert(0, 'Peringkat', range(1, len(df_rank_print) + 1))
    cw_res = [20, 70, 40, 40]
    pdf.simple_table(df_rank_print[['Peringkat', 'Alternatif', 'Nilai Si (Total)', 'Nilai Ki (Utilitas)']], cw_res)

    pdf.ln(5)
    pdf.section_title("KESIMPULAN")
    pdf.set_font('Arial', '', 11)
    # Kotak kesimpulan seperti gambar
    pdf.set_fill_color(240, 240, 255)
    pdf.multi_cell(0, 10, f"Berdasarkan perhitungan metode ARAS:\nSmartphone terbaik adalah {best_choice['nama']} dengan nilai Ki = {best_choice['skor']:.4f}.\nAlternatif ini memiliki spesifikasi seimbang dengan harga yang kompetitif dibandingkan nilai optimal.", 1, 'L', 1)

    return pdf.output(dest='S').encode('latin-1')

# --- DATA & SETUP AWAL (HARDCODED SESUAI GAMBAR) ---
# Bobot persis gambar image_7110f7.png
bobot_fix = {
    'Price': 0.30, 
    'RAM': 0.15, 
    'ROM': 0.15, 
    'Battery': 0.15, 
    'Camera': 0.25 
}

# Data persis gambar image_711100.png
data_fix = {
    'Alternative': ['Samsung A54', 'Xiaomi 13T', 'Infinix GT 10 Pro', 'Realme 11 Pro'],
    'Price': [5.9, 6.5, 4.4, 5.5],
    'RAM': [8, 12, 8, 12],
    'ROM': [256, 256, 256, 512],
    'Battery': [5000, 5000, 5000, 5000],
    'Camera': [50, 50, 108, 100]
}

# --- HEADER APP ---
st.title("📱 Perhitungan SPK ARAS (Mode Presentasi)")
st.markdown("Aplikasi ini mensimulasikan perhitungan **persis seperti slide presentasi** yang Anda lampirkan.")

# --- SIDEBAR (HANYA DISPLAY, NON-EDITABLE AGAR KONSISTEN DGN GAMBAR) ---
st.sidebar.header("Parameter Studi Kasus")
st.sidebar.info("Parameter dikunci sesuai gambar agar hasil 100% akurat.")
df_bobot_show = pd.DataFrame({
    'Kode': ['C1', 'C2', 'C3', 'C4', 'C5'],
    'Kriteria': ['Price', 'RAM', 'ROM', 'Battery', 'Camera'],
    'Tipe': ['Cost', 'Benefit', 'Benefit', 'Benefit', 'Benefit'],
    'Bobot (W)': [0.30, 0.15, 0.15, 0.15, 0.25]
})
st.sidebar.table(df_bobot_show)

# --- PROSES HITUNG (Langsung dijalankan untuk display) ---
df = pd.DataFrame(data_fix)
alternatives = df['Alternative'].values
matrix = df.drop('Alternative', axis=1)
cols = matrix.columns
types = ['cost', 'benefit', 'benefit', 'benefit', 'benefit'] # C1 Cost, others Benefit

# 1. OPTIMAL (X0)
x0 = []
for i, col in enumerate(cols):
    if types[i] == 'benefit':
        x0.append(matrix[col].max())
    else:
        x0.append(matrix[col].min())

df_calc = matrix.copy()
df_x0 = pd.DataFrame([x0], columns=cols)
df_step1 = pd.concat([df_x0, df_calc], ignore_index=True) # Tabel Langkah 1

# 2. NORMALISASI (R)
df_step2 = df_step1.copy().astype(float)
for i, col in enumerate(cols):
    if types[i] == 'benefit':
        df_step2[col] = df_step1[col] / df_step1[col].sum()
    else:
        # Cost Logic
        reciprocal = 1 / df_step1[col]
        df_step2[col] = reciprocal / reciprocal.sum()

# 3. PEMBOBOTAN (D)
df_step3 = df_step2.copy()
bobot_list = list(bobot_fix.values())
for i, col in enumerate(cols):
    df_step3[col] = df_step2[col] * bobot_list[i]

# Hitung Si
Si = df_step3.sum(axis=1)
df_step3['Total (Si)'] = Si # Tambah kolom Si untuk display

# 4. UTILITAS (Ki)
S0 = Si[0]
Ki = Si / S0

# HASIL FINAL
final_res = pd.DataFrame({
    'Alternatif': ['OPTIMAL (A0)'] + list(alternatives),
    'Nilai Si (Total)': Si,
    'Nilai Ki (Utilitas)': Ki
})
final_rank = final_res.iloc[1:].copy()
final_rank = final_rank.sort_values(by='Nilai Ki (Utilitas)', ascending=False).reset_index(drop=True)
best_hp = final_rank.iloc[0]

# --- RENDER TAMPILAN WEB (MIRIP GAMBAR) ---

# Section 1: Data
st.markdown('<div class="step-header">STUDI KASUS (DATA SMARTPHONE)</div>', unsafe_allow_html=True)
st.markdown("Berikut adalah data alternatif smartphone yang akan dianalisis:")
st.dataframe(df)

# Section 2: Kriteria
st.markdown('<div class="step-header">ANALISIS KRITERIA DAN BOBOT</div>', unsafe_allow_html=True)
st.markdown("Bobot dan jenis kriteria ditentukan sebagai berikut:")
st.table(df_bobot_show)

# Section 3: Langkah 1
st.markdown('<div class="step-header">LANGKAH 1 - MATRIKS KEPUTUSAN & NILAI OPTIMUM (A0)</div>', unsafe_allow_html=True)
st.markdown("""
* Menentukan nilai Optimum ($A_0$) berdasarkan prinsip **Max** untuk Benefit dan **Min** untuk Cost.
* Lihat baris paling atas ($A_0$):
""")
# Display Step 1 Table with index rename
df_display_s1 = df_step1.copy()
df_display_s1.index = ['A0 (Optimum)', 'A1', 'A2', 'A3', 'A4']
st.dataframe(df_display_s1)

# Section 4: Langkah 2
st.markdown('<div class="step-header">LANGKAH 2 - HASIL NORMALISASI LENGKAP (R)</div>', unsafe_allow_html=True)
st.markdown("""
* Perhitungan khusus **Cost (Price)**: Nilai diubah ke $1/x$ lalu dibagi total.
* Perhitungan **Benefit**: Nilai dibagi total kolom.
* Hasil Normalisasi:
""")
df_display_s2 = df_step2.copy()
df_display_s2.index = ['A0', 'A1', 'A2', 'A3', 'A4']
st.dataframe(df_display_s2.style.format("{:.3f}"))

# Section 5: Langkah 3
st.markdown('<div class="step-header">LANGKAH 3 - MATRIKS TERBOBOT (D)</div>', unsafe_allow_html=True)
st.markdown("""
* Mengalikan nilai normalisasi dengan bobot ($W$).
* Menghasilkan **Total ($S_i$)** di kolom kanan.
""")
df_display_s3 = df_step3.copy()
df_display_s3.index = ['S0', 'S1', 'S2', 'S3', 'S4']
st.dataframe(df_display_s3.style.format("{:.3f}"))

# Section 6: Langkah 4 & 5
st.markdown('<div class="step-header">LANGKAH 4 & 5 - UTILITAS (Ki) DAN PERANGKINGAN</div>', unsafe_allow_html=True)
st.markdown(f"Menghitung Derajat Utilitas $K_i = S_i / S_0$ (dimana $S_0 = {S0:.3f}$):")

# Tampilan manual calculation text mirip gambar
st.info(f"""
**Detail Perhitungan Ki:**
* **{final_rank.iloc[0]['Alternatif']}**: {final_rank.iloc[0]['Nilai Si (Total)']:.3f} / {S0:.3f} = **{final_rank.iloc[0]['Nilai Ki (Utilitas)']:.3f}** (Juara 1)
* **{final_rank.iloc[1]['Alternatif']}**: {final_rank.iloc[1]['Nilai Si (Total)']:.3f} / {S0:.3f} = **{final_rank.iloc[1]['Nilai Ki (Utilitas)']:.3f}**
* dst...
""")

st.markdown("### 🏆 Hasil Akhir")
st.dataframe(final_rank.style.format({'Nilai Si (Total)': '{:.3f}', 'Nilai Ki (Utilitas)': '{:.3f}'}))

# Section: Kesimpulan
st.markdown('<div class="step-header">KESIMPULAN</div>', unsafe_allow_html=True)
st.success(f"""
Berdasarkan perhitungan metode ARAS dengan bobot yang ditentukan:
1.  **Peringkat 1: {best_hp['Alternatif']} (Ki = {best_hp['Nilai Ki (Utilitas)']:.3f})**
2.  Peringkat 2: {final_rank.iloc[1]['Alternatif']}
3.  Peringkat 3: {final_rank.iloc[2]['Alternatif']}
4.  Peringkat 4: {final_rank.iloc[3]['Alternatif']}

**{best_hp['Alternatif']}** menjadi alternatif terbaik karena memiliki spesifikasi (terutama Kamera & ROM) yang tinggi dengan harga yang masih kompetitif dibandingkan nilai optimal.
""")

# --- BUTTON DOWNLOAD ---
st.markdown("---")
pdf_bytes = create_slide_pdf(
    data_input=df,
    bobot_df=df_bobot_show,
    df_step1=df_step1,
    df_step2=df_step2,
    df_step3=df_step3,
    df_ranking=final_rank,
    best_choice={"nama": best_hp['Alternatif'], "skor": best_hp['Nilai Ki (Utilitas)']}
)

col1, col2 = st.columns([1, 4])
with col1:
    st.download_button(
        label="📄 Download Laporan PDF",
        data=pdf_bytes,
        file_name="Laporan_ARAS_Slide_Style.pdf",
        mime="application/pdf"
    )
with col2:
    st.caption("Klik tombol ini untuk mengunduh laporan dengan format yang **persis** mengikuti alur slide presentasi di atas.")
