import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from fpdf import FPDF
from datetime import datetime

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="SPK ARAS - Fully Dynamic", page_icon="📱", layout="wide")

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
    </style>
""", unsafe_allow_html=True)

# --- INITIALIZE SESSION STATE (DATABASE SEMENTARA) ---
# Ini agar data kriteria tersimpan meskipun tombol ditekan
if 'kriteria_config' not in st.session_state:
    st.session_state['kriteria_config'] = [
        {"nama": "Price",   "tipe": "cost",    "bobot": 0.30},
        {"nama": "RAM",     "tipe": "benefit", "bobot": 0.15},
        {"nama": "ROM",     "tipe": "benefit", "bobot": 0.15},
        {"nama": "Battery", "tipe": "benefit", "bobot": 0.15},
        {"nama": "Camera",  "tipe": "benefit", "bobot": 0.25},
    ]

if 'data_smartphone' not in st.session_state:
    # Data awal default
    st.session_state['data_smartphone'] = pd.DataFrame([
        ["Samsung Galaxy A54",  5.9, 8,  256, 5000, 50],
        ["Xiaomi 13T",          6.5, 12, 256, 5000, 50],
        ["Infinix GT 10 Pro",   4.4, 8,  256, 5000, 108],
        ["Realme 11 Pro",       5.5, 12, 512, 5000, 100],
    ], columns=["Alternative", "Price", "RAM", "ROM", "Battery", "Camera"])

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
            self.set_font('Arial', 'B', 7)
            cols = df.columns
            if not col_widths: col_widths = [190 / len(cols)] * len(cols)
            for i, col in enumerate(cols):
                # Truncate nama kolom panjang agar tidak error di PDF
                col_name = str(col)[:8] 
                self.cell(col_widths[i], 6, col_name, 1, 0, 'C')
            self.ln()
            self.set_font('Arial', '', 7)
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
    pdf.simple_table(data_input)
    
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
    
    # Custom width untuk hasil akhir
    pdf.simple_table(df_rank_p[['Rank', 'Kode', 'Alternatif', 'Nilai Ki (Utilitas)']], [15, 20, 60, 35])
    
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f"Rekomendasi Terbaik: {best_hp['nama']} (Kode: {best_hp['kode']})", 0, 1)

    return pdf.output(dest='S').encode('latin-1')

# --- SIDEBAR: MANAJEMEN KRITERIA ---
st.sidebar.header("🔧 Kelola Kriteria")

with st.sidebar.expander("➕ Tambah / ➖ Hapus Kriteria"):
    # Form Tambah
    with st.form("add_criteria_form"):
        st.write("**Tambah Kriteria Baru**")
        new_crit_name = st.text_input("Nama Kriteria (Contoh: Layar)")
        new_crit_type = st.selectbox("Tipe", ["benefit", "cost"])
        submitted = st.form_submit_button("Tambahkan")
        
        if submitted and new_crit_name:
            # Cek duplikat
            existing_names = [item['nama'] for item in st.session_state['kriteria_config']]
            if new_crit_name in existing_names:
                st.error("Kriteria sudah ada!")
            else:
                # Update Config
                st.session_state['kriteria_config'].append({
                    "nama": new_crit_name, 
                    "tipe": new_crit_type, 
                    "bobot": 0.0 # Default 0 agar user set sendiri nanti
                })
                # Update DataFrame (Tambah kolom baru dengan nilai 0)
                st.session_state['data_smartphone'][new_crit_name] = 0
                st.rerun()

    # Form Hapus
    st.write("---")
    st.write("**Hapus Kriteria**")
    existing_criteria = [item['nama'] for item in st.session_state['kriteria_config']]
    crit_to_remove = st.selectbox("Pilih kriteria untuk dihapus", ["-- Pilih --"] + existing_criteria)
    
    if st.button("Hapus Kriteria Terpilih"):
        if crit_to_remove != "-- Pilih --":
            # Hapus dari config
            st.session_state['kriteria_config'] = [
                item for item in st.session_state['kriteria_config'] if item['nama'] != crit_to_remove
            ]
            # Hapus dari DataFrame
            if crit_to_remove in st.session_state['data_smartphone'].columns:
                st.session_state['data_smartphone'] = st.session_state['data_smartphone'].drop(columns=[crit_to_remove])
            st.rerun()

# --- SIDEBAR: SLIDER BOBOT DINAMIS ---
st.sidebar.header("⚙️ Atur Bobot")

current_weights = {}
weight_values = []

for item in st.session_state['kriteria_config']:
    nama = item['nama']
    tipe = item['tipe']
    # Slider dinamis
    val = st.sidebar.slider(
        f"{nama} ({tipe})", 
        0.0, 1.0, 
        float(item['bobot']), 
        0.05,
        key=f"slider_{nama}" # Key unik agar tidak bentrok
    )
    current_weights[nama] = val
    weight_values.append(val)
    # Update state bobot (agar tersimpan saat rerun)
    item['bobot'] = val

total_bobot = round(sum(weight_values), 2)
st.sidebar.markdown("---")
st.sidebar.write(f"**Total Bobot:** {total_bobot}")

is_overload = False
if total_bobot > 1.0:
    st.sidebar.error("❌ Total > 1.0 (Harap kurangi)")
    is_overload = True
elif total_bobot < 1.0:
    st.sidebar.warning("⚠️ Total < 1.0")
else:
    st.sidebar.success("✅ Total Pas 1.0")


# --- HALAMAN UTAMA ---
st.title("📱 SPK Smartphone - User Customizable")
st.write("Gunakan menu **'Kelola Kriteria'** di sidebar untuk menambah/menghapus kolom kriteria.")

# Tampilkan Tabel Editable dari Session State
# User mengisi nilai kriteria baru disini
edited_df = st.data_editor(st.session_state['data_smartphone'], num_rows="dynamic", use_container_width=True)

# Simpan perubahan data tabel kembali ke session state
# (Agar kalau nambah kriteria lagi, data yang diketik tidak hilang)
st.session_state['data_smartphone'] = edited_df

# --- ENGINE PERHITUNGAN ---
if is_overload:
    st.button("🚀 Hitung & Tampilkan", type="primary", disabled=True)
else:
    if st.button("🚀 Hitung & Tampilkan", type="primary"):
        
        # Ambil Data
        alts = edited_df['Alternative'].values
        # Ambil hanya kolom kriteria (drop Alternative)
        criteria_cols = [item['nama'] for item in st.session_state['kriteria_config']]
        
        # Pastikan kolom tabel sesuai dengan config (Safety check)
        try:
            matrix = edited_df[criteria_cols]
        except KeyError:
            st.error("Terjadi ketidakcocokan data kolom. Silakan refresh halaman.")
            st.stop()

        types = [item['tipe'] for item in st.session_state['kriteria_config']]
        bobot_list = [current_weights[c] for c in criteria_cols]

        # 1. Menentukan X0
        x0 = []
        for i, col in enumerate(criteria_cols):
            if types[i] == 'benefit':
                x0.append(matrix[col].max())
            else:
                x0.append(matrix[col].min())
                
        df_calc = matrix.copy()
        df_x0 = pd.DataFrame([x0], columns=criteria_cols)
        df_step1 = pd.concat([df_x0, df_calc], ignore_index=True)

        # 2. Normalisasi
        df_step2 = df_step1.copy().astype(float)
        for i, col in enumerate(criteria_cols):
            # Hindari pembagian dengan nol
            if df_step1[col].sum() == 0:
                df_step2[col] = 0
                continue
                
            if types[i] == 'benefit':
                df_step2[col] = df_step1[col] / df_step1[col].sum()
            else:
                # Handle Cost 0
                reciprocal = df_step1[col].apply(lambda x: 1/x if x!=0 else 0)
                if reciprocal.sum() == 0:
                    df_step2[col] = 0
                else:
                    df_step2[col] = reciprocal / reciprocal.sum()

        # 3. Pembobotan
        df_step3 = df_step2.copy()
        for i, col in enumerate(criteria_cols):
            df_step3[col] = df_step2[col] * bobot_list[i]
        
        Si = df_step3.sum(axis=1)
        df_step3['Total (Si)'] = Si

        # 4. Utilitas
        S0 = Si[0]
        if S0 == 0:
            Ki = Si * 0 # Hindari error jika S0 nol
        else:
            Ki = Si / S0

        # 5. Hasil
        kode_awal = ['A0'] + [f"A{i+1}" for i in range(len(alts))]
        res = pd.DataFrame({
            'Kode': kode_awal,
            'Alternatif': ['OPTIMAL (A0)'] + list(alts),
            'Nilai Si (Total)': Si,
            'Nilai Ki (Utilitas)': Ki
        })
        
        # Split Data
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
        
        st.success(f"🏆 Juara 1: **{best['Alternatif']}** (Kode Asal: **{best['Kode']}**)")

        st.markdown("---")
        pdf_bytes = create_dynamic_pdf(edited_df, current_weights, df_step1, df_step2, df_step3, rank_df, 
                                       {"nama": best['Alternatif'], "kode": best['Kode']})
        
        st.download_button(
            label="📄 Download Laporan Lengkap (PDF)",
            data=pdf_bytes,
            file_name="Laporan_ARAS_Custom.pdf",
            mime="application/pdf"
        )
