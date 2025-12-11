import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
from datetime import datetime

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="SPK ARAS Smartphone",
    page_icon="📱",
    layout="wide"
)

# --- FUNGSI GENERATE PDF DETAIL ---
def create_detailed_pdf(data_input, weights, matrix_x0, matrix_norm, matrix_weighted, final_rank, best_choice):
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 14)
            self.cell(0, 10, 'Laporan Detail SPK - Metode ARAS', 0, 1, 'C')
            self.set_font('Arial', 'I', 8)
            self.cell(0, 5, f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 1, 'C')
            self.ln(10)

        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Halaman {self.page_no()}', 0, 0, 'C')

        def chapter_title(self, label):
            self.set_font('Arial', 'B', 11)
            self.set_fill_color(230, 230, 230)
            self.cell(0, 8, label, 0, 1, 'L', 1)
            self.ln(2)

        def simple_table(self, df, col_widths=None):
            # Header
            self.set_font('Arial', 'B', 9)
            cols = df.columns
            if not col_widths:
                col_widths = [190 / len(cols)] * len(cols)
            
            for i, col in enumerate(cols):
                self.cell(col_widths[i], 7, str(col), 1, 0, 'C')
            self.ln()
            
            # Data
            self.set_font('Arial', '', 9)
            for index, row in df.iterrows():
                for i, col in enumerate(cols):
                    val = row[col]
                    # Format float jika perlu
                    if isinstance(val, (float, np.floating)):
                        val = f"{val:.4f}"
                    self.cell(col_widths[i], 7, str(val), 1, 0, 'C')
                self.ln()
            self.ln(5)

    pdf = PDF()
    pdf.add_page()
    
    # 1. KONFIGURASI BOBOT
    pdf.chapter_title("1. Konfigurasi Bobot Kriteria")
    pdf.set_font("Arial", size=10)
    w_text = ", ".join([f"{k}: {v}" for k, v in weights.items()])
    pdf.multi_cell(0, 5, f"Bobot yang digunakan: {w_text}")
    pdf.ln(5)

    # 2. DATA INPUT
    pdf.chapter_title("2. Data Awal Alternatif")
    # Tentukan lebar kolom manual agar rapi
    # Asumsi kolom: Alternative, Price, RAM, ROM, Battery, Camera
    cw_input = [45, 25, 25, 25, 30, 30] 
    pdf.simple_table(data_input, col_widths=cw_input)

    # 3. MATRIKS X0
    pdf.chapter_title("3. Matriks Keputusan & Nilai Optimal (X0)")
    pdf.set_font("Arial", 'I', 8)
    pdf.cell(0, 5, "Baris paling atas (indeks 0) adalah nilai Optimal (X0).", 0, 1)
    pdf.ln(2)
    # Gunakan nama kolom saja tanpa 'Alternative' jika matrix_x0 hanya angka
    # Kita perlu memastikan formatnya rapi. 
    # Karena matrix_x0 di logic bawah tidak punya kolom 'Alternative', kita print apa adanya.
    # Untuk laporan, lebih baik kita tampilkan dengan jelas.
    
    # Trik: Tambahkan label baris untuk PDF
    df_print_x0 = matrix_x0.copy()
    if 'Alternative' not in df_print_x0.columns:
        # Buat list nama baris: X0, A1, A2, dst
        row_labels = ['X0 (Optimal)'] + [f"A{i+1}" for i in range(len(df_print_x0)-1)]
        df_print_x0.insert(0, 'Label', row_labels)
        cw_x0 = [25, 30, 25, 25, 30, 30] # Sesuaikan jumlah kolom
    else:
        cw_x0 = cw_input

    pdf.simple_table(df_print_x0, col_widths=cw_x0)

    # 4. NORMALISASI (R)
    pdf.chapter_title("4. Matriks Normalisasi (R)")
    pdf.set_font("Arial", 'I', 8)
    pdf.multi_cell(0, 5, "Nilai dinormalisasi berdasarkan jenis kriteria (Benefit / Cost).")
    pdf.ln(2)
    pdf.simple_table(df_print_x0.iloc[:, 0:1].join(matrix_norm), col_widths=cw_x0)

    # 5. PEMBOBOTAN (D)
    pdf.chapter_title("5. Matriks Terbobot (D)")
    pdf.simple_table(df_print_x0.iloc[:, 0:1].join(matrix_weighted), col_widths=cw_x0)

    # 6. HASIL AKHIR
    pdf.add_page() # Pindah halaman untuk hasil akhir agar tidak terpotong
    pdf.chapter_title("6. Hasil Akhir & Perangkingan")
    
    # Persiapan tabel hasil
    df_res_print = final_rank.copy()
    # Tambahkan kolom Ranking
    df_res_print.insert(0, 'Rank', range(1, len(df_res_print) + 1))
    
    cw_res = [15, 60, 40, 40] # Rank, Alt, Si, Ki
    pdf.simple_table(df_res_print[['Rank', 'Alternatif', 'Nilai Si (Total)', 'Nilai Ki (Utilitas)']], col_widths=cw_res)

    # 7. KESIMPULAN
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 10, "KESIMPULAN:", 0, 1)
    pdf.set_font("Arial", size=11)
    pdf.set_text_color(0, 100, 0) # Warna hijau gelap
    text_kesimpulan = (
        f"Berdasarkan perhitungan metode ARAS, smartphone terbaik adalah "
        f"{best_choice['nama']} (Rank 1) dengan Nilai Utilitas {best_choice['skor']:.4f}."
    )
    pdf.multi_cell(0, 8, text_kesimpulan)
    pdf.set_text_color(0, 0, 0) # Reset warna

    return pdf.output(dest='S').encode('latin-1')


# --- MAIN APP LOGIC ---

# Judul & Deskripsi
st.title("📱 SPK Pemilihan Smartphone - Metode ARAS")
st.markdown("""
Aplikasi ini menggunakan metode **Additive Ratio Assessment (ARAS)**.
Laporan PDF yang dihasilkan kini mencakup **detail perhitungan step-by-step**.
""")

# Sidebar Input Bobot
st.sidebar.header("⚙️ Konfigurasi Bobot")
w_Price = st.sidebar.slider("Bobot Price (Cost)", 0.0, 0.5, 0.30, 0.05)
w_ram = st.sidebar.slider("Bobot RAM (Benefit)", 0.0, 0.5, 0.20, 0.05)
w_rom = st.sidebar.slider("Bobot ROM (Benefit)", 0.0, 0.5, 0.20, 0.05)
w_Battery = st.sidebar.slider("Bobot Battery (Benefit)", 0.0, 0.5, 0.15, 0.05)
w_Camera = st.sidebar.slider("Bobot Camera (Benefit)", 0.0, 0.5, 0.15, 0.05)

bobot = [w_Price, w_ram, w_rom, w_Battery, w_Camera]
total_bobot = sum(bobot)
st.sidebar.write(f"**Total Bobot:** {total_bobot:.2f}")

bobot_dict = {
    "Price (Cost)": w_Price, "RAM": w_ram, "ROM": w_rom, 
    "Battery": w_Battery, "Camera": w_Camera
}

# Data Awal
data_awal = {
    'Alternative': ['Samsung Galaxy A54', 'Xiaomi 13T', 'Infinix GT 10 Pro', 'Realme 11 Pro'],
    'Price': [5.9, 6.5, 4.4, 5.5],
    'RAM': [8, 12, 8, 12],
    'ROM': [256, 256, 256, 512],
    'Battery': [5000, 5000, 5000, 5000],
    'Camera': [50, 50, 108, 100]
}

st.subheader("1. Data Alternatif Smartphone")
df = pd.DataFrame(data_awal)
df_edit = st.data_editor(df, num_rows="dynamic", key="data_editor")

if st.button("🚀 Hitung & Siapkan Laporan"):
    
    # --- LOGIC PERHITUNGAN ARAS ---
    alternatives = df_edit['Alternative'].values
    matrix = df_edit.drop('Alternative', axis=1)
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
    df_lengkap = pd.concat([df_x0, df_calc], ignore_index=True) # Matriks X lengkap
    
    # 2. Normalisasi
    df_norm = df_lengkap.copy().astype(float)
    for i, col in enumerate(cols):
        if types[i] == 'benefit':
            df_norm[col] = df_lengkap[col] / df_lengkap[col].sum()
        else:
            reciprocal = 1 / df_lengkap[col]
            df_norm[col] = reciprocal / reciprocal.sum()
            
    # 3. Pembobotan
    df_weighted = df_norm.copy()
    for i, col in enumerate(cols):
        df_weighted[col] = df_norm[col] * bobot[i]

    # 4. Nilai Akhir
    Si = df_weighted.sum(axis=1)
    S0 = Si[0] 
    Ki = Si / S0
    
    # Ranking
    final_res = pd.DataFrame({
        'Alternatif': ['OPTIMAL (X0)'] + list(alternatives),
        'Nilai Si (Total)': Si,
        'Nilai Ki (Utilitas)': Ki
    })
    
    final_ranking = final_res.iloc[1:].copy()
    final_ranking = final_ranking.sort_values(by='Nilai Ki (Utilitas)', ascending=False).reset_index(drop=True)
    
    best_hp = final_ranking.iloc[0]['Alternatif']
    best_score = final_ranking.iloc[0]['Nilai Ki (Utilitas)']

    # --- TAMPILAN WEB ---
    st.write("---")
    st.success(f"Rekomendasi Terbaik: **{best_hp}** ({best_score:.4f})")
    
    tab1, tab2, tab3 = st.tabs(["🏆 Hasil Ranking", "📊 Detail Matriks", "📈 Grafik"])
    
    with tab1:
        st.dataframe(final_ranking.style.format({'Nilai Si (Total)': '{:.4f}', 'Nilai Ki (Utilitas)': '{:.4f}'}))
        
    with tab2:
        st.write("**Matriks Normalisasi (R):**")
        st.dataframe(df_norm)
        st.write("**Matriks Terbobot (D):**")
        st.dataframe(df_weighted)
        
    with tab3:
        st.bar_chart(final_ranking.set_index('Alternatif')['Nilai Ki (Utilitas)'])

    # --- DOWNLOAD PDF DETAIL ---
    st.write("---")
    st.subheader("🖨️ Cetak Laporan Lengkap")
    
    pdf_bytes = create_detailed_pdf(
        data_input=df_edit,
        weights=bobot_dict,
        matrix_x0=df_lengkap,      # Kirim matriks lengkap (X0 + Data)
        matrix_norm=df_norm,       # Kirim matriks normalisasi
        matrix_weighted=df_weighted, # Kirim matriks terbobot
        final_rank=final_ranking,
        best_choice={"nama": best_hp, "skor": best_score}
    )
    
    st.download_button(
        label="📥 Download Laporan Detail (PDF)",
        data=pdf_bytes,
        file_name=f"Laporan_ARAS_Detail_{datetime.now().strftime('%Y%m%d')}.pdf",
        mime="application/pdf"
    )
