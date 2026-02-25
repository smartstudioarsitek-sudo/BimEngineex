import json
import google.generativeai as genai
import streamlit as st

def ai_parse_structural_data(text_content, api_key):
    """
    Super-Extractor v2: Menggunakan fitur native JSON dari Gemini.
    Dijamin 100% tidak ada teks nyasar atau ngeles.
    """
    if not api_key:
        return None

    genai.configure(api_key=api_key)
    
    # 🌟 JURUS PAMUNGKAS: Paksa AI HANYA membalas dengan JSON
    generation_config = genai.GenerationConfig(
        response_mime_type="application/json"
    )
    
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        generation_config=generation_config
    )
    
    prompt = f"""
    Anda adalah Senior Quantity Surveyor.
    Ekstrak data Bill of Quantities (BOQ) dari teks dokumen berikut.
    Jika ini adalah dokumen BOQ, ambil nama pekerjaan dan volumenya.
    Jika ini adalah DED/Gambar, hitung volumenya dari dimensi dan jumlah yang tertera.
    
    Teks Dokumen:
    ---
    {text_content[:20000]}
    ---
    
    WAJIB kembalikan ARRAY JSON dengan skema baku berikut ini:
    [
        {{"Kategori": "Nama Divisi/Kategori", "Nama": "Nama Uraian Pekerjaan", "Volume": 10.5}}
    ]
    *Penting: 'Volume' HARUS berupa angka desimal (float) yang menggunakan titik (.), BUKAN koma. Jangan gunakan string untuk volume.
    """
    
    try:
        response = model.generate_content(prompt)
        
        # Karena kita sudah pakai response_mime_type, output PASTI berupa JSON bersih
        data_boq = json.loads(response.text)
        return data_boq
        
    except Exception as e:
        # Jika gagal, kita tampilkan error-nya langsung di layar Streamlit kakak
        # Agar ketahuan si AI salah di mana
        st.error(f"🚨 Gagal menyusun tabel JSON. Error: {e}")
        try:
            st.info(f"Teks mentah dari AI: {response.text}")
        except:
            pass
        return None
