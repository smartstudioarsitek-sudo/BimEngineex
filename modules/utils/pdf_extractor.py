# modules/utils/pdf_extractor.py
import pdfplumber
import re
import streamlit as st
import json
import google.generativeai as genai

def extract_text_from_pdf(uploaded_file):
    """
    Lebih cerdas mengekstrak tabel dan layout menggunakan pdfplumber.
    Cocok untuk laporan teknik yang banyak mengandung tabel.
    """
    text = ""
    try:
        # pdfplumber butuh file path atau file-like object
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                # 1. STRATEGI TABEL: Ambil data tabel terlebih dahulu
                # Laporan struktur 80% datanya ada di tabel
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        # Bersihkan None values dan gabung dengan delimiter pipa |
                        # Ini membantu AI membedakan kolom
                        clean_row = [str(cell) if cell is not None else "" for cell in row]
                        text += " | ".join(clean_row) + "\n"
                
                text += "\n--- TEKS HALAMAN ---\n"
                
                # 2. STRATEGI TEKS: Ambil sisa teks biasa
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                    
        return text
    except Exception as e:
        return f"Error membaca PDF: {e}"

def ai_parse_structural_data(text_content, api_key):
    """
    Super-Extractor: Mampu membaca Tabel BOQ matang maupun menghitung dari Teks/Legenda DED.
    """
    if not api_key:
        return None

    genai.configure(api_key=api_key)
    # Gunakan flash karena cepat dan tokennya besar
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # SUPER PROMPT (SOP Quantity Surveyor AI)
    prompt = f"""
    Anda adalah Senior Quantity Surveyor (QS) dan AI Data Gatekeeper.
    Tugas Anda: Ekstrak informasi Bill of Quantities (BOQ) dari teks dokumen yang diberikan. 
    
    Dokumen ini bisa memiliki 2 kemungkinan format:
    SKENARIO 1 (TABEL BOQ): Jika teks berisi tabel RAB/BOQ (ada Uraian Pekerjaan dan Volume), langsung ekstrak nama pekerjaan dan angka volumenya secara presisi.
    SKENARIO 2 (DED / LAPORAN DESAIN): Jika teks berisi legenda dimensi (misal K1=400x400) dan rekap jumlah tiang/balok, hitung estimasi volumenya (Panjang x Lebar x Tinggi x Jumlah). Jika ada data parameter struktur (fc, fy, Mu, Pu), abaikan saja.
    
    Teks Dokumen:
    ---
    {text_content[:20000]} # Limitasi dinaikkan agar muat membaca PDF BOQ yang panjang
    ---
    
    INSTRUKSI OUTPUT:
    Kembalikan HANYA format array JSON murni, tanpa teks pembuka, tanpa penutup, tanpa block markdown (```json).
    Format Wajib:
    [
        {{"Kategori": "Pekerjaan Tanah", "Nama": "Galian Tanah Pondasi", "Volume": 166.37}},
        {{"Kategori": "Struktur Beton", "Nama": "Kolom K1 (400x400)", "Volume": 9.22}}
    ]
    *Catatan: Pastikan 'Volume' adalah angka float, BUKAN string. Jika volume gagal didapat, berikan nilai 1.0.
    """
    
    try:
        response = model.generate_content(prompt)
        # Pembersihan ekstra agar JSON tidak error saat di-load
        clean_json = response.text.replace("```json", "").replace("```", "").strip()
        
        # Ekstrak array JSON menggunakan Regex jika AI bandel menyelipkan teks penjelasan
        match = re.search(r'\[.*\]', clean_json, re.DOTALL)
        if match:
            clean_json = match.group(0)
            
        data_boq = json.loads(clean_json)
        return data_boq
        
    except Exception as e:
        print(f"Gagal memparsing respons AI ke JSON: {e}")
        return None
        clean_json = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)
    except Exception as e:
        # st.error(f"Gagal parsing AI: {e}") # Silent error agar UI tidak berantakan
        return None
