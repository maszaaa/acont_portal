import jwt
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
import re
import sqlite3
import calendar

app = FastAPI(title="ACONT API Backend - Secured (JWT)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 0. KONFIGURASI KEAMANAN (JWT) - BARU
# ==========================================
SECRET_KEY = "ACONT_RAHASIA_NEGARA_PKN_STAN_2026" # Gunakan key yang kuat di versi production
ALGORITHM = "HS256"
security = HTTPBearer()

def create_access_token(data: dict):
    to_encode = data.copy()
    # Token berlaku selama 2 jam
    expire = datetime.now(timezone.utc) + timedelta(hours=2)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        # Dekripsi token dari header Authorization: Bearer <token>
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Sesi login telah berakhir, silakan login ulang.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token otentikasi tidak valid atau telah dimanipulasi.")

# ==========================================
# 1. SETUP DATABASE SQLITE (PENYIMPANAN & MAPRES)
# ==========================================
DB_FILE = "acont_database.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mapres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            npm TEXT,
            nama TEXT,
            nama_prestasi TEXT,
            kategori TEXT,
            tingkat TEXT,
            link_bukti TEXT DEFAULT '-',
            status TEXT DEFAULT 'Pending',
            skor INTEGER DEFAULT 0,
            alasan_tolak TEXT DEFAULT '-'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mahasiswa_stats (
            npm TEXT PRIMARY KEY,
            nama TEXT,
            ipk REAL DEFAULT 0.0,
            siku REAL DEFAULT 0.0,
            skpm REAL DEFAULT 0.0,
            is_kandidat INTEGER DEFAULT 0 
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            waktu DATETIME DEFAULT CURRENT_TIMESTAMP,
            aktor TEXT,
            aksi TEXT,
            detail TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ==========================================
# 2. LOGIKA AUTO-LOCK DEADLINE MAPRES
# ==========================================
def cek_status_waktu_pengajuan():
    sekarang = datetime.now()
    _, hari_terakhir = calendar.monthrange(sekarang.year, sekarang.month)
    batas_waktu = datetime(sekarang.year, sekarang.month, hari_terakhir, 15, 0, 0)
    if sekarang > batas_waktu: return False
    return True

# ==========================================
# 3. MODEL DATA PENGIRIMAN
# ==========================================
class LoginRequest(BaseModel):
    npm: str
    password: str

class DaftarKandidatRequest(BaseModel):
    npm: str

class AjukanMapresRequest(BaseModel):
    npm: str
    nama: str
    nama_prestasi: str
    kategori: str
    tingkat: str
    link_bukti: str 

class VerifikasiMapresRequest(BaseModel):
    id_pengajuan: int
    keputusan: str
    alasan: str = ""

# ==========================================
# 4. FUNGSI SCRAPING
# ==========================================
BASE_URL = "https://portal.pknstan.ac.id"
LANDING_URL = f"{BASE_URL}/"
LOGIN_ACTION_URL = f"{BASE_URL}/auth/masuk"
NILAI_URL = f"{BASE_URL}/stud/nilai"
SKPM_DASHBOARD_URL = f"{BASE_URL}/stud/skpmvd/dashboard"
SKPM_DATA_URL = f"{BASE_URL}/stud/skpmvd/kelolaskpm"

def login_portal(session: requests.Session, npm: str, password: str) -> tuple[bool, str]:
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
        "Upgrade-Insecure-Requests": "1"
    })
    
    try:
        session.get(LANDING_URL, timeout=15)
    except Exception as e:
        return False, f"Server Portal STAN sedang down: {str(e)}"

    payload = {"identity": npm, "password": password, "submit": "Masuk"}

    session.headers.update({
        "Origin": BASE_URL,
        "Referer": LANDING_URL,
        "Content-Type": "application/x-www-form-urlencoded"
    })
    
    login_resp = session.post(LOGIN_ACTION_URL, data=payload, timeout=15)
    soup_after = BeautifulSoup(login_resp.text, "html.parser")
    
    is_success = "auth/masuk" not in login_resp.url or soup_after.find("input", {"name": "identity"}) is None
    
    if is_success:
        return True, "Login Berhasil"
    else:
        return False, "NPM atau Password yang dimasukkan salah."

def scrape_data(session: requests.Session):
    # --- Identitas & Nilai ---
    resp_nilai = session.get(NILAI_URL)
    soup_nilai = BeautifulSoup(resp_nilai.text, "html.parser")
    
    title_card = soup_nilai.select_one(".main-card .card-body")
    identitas = {}
    if title_card:
        heading = title_card.find("h5", class_="text-primary")
        nama_el = title_card.find_all("h5")[-1] if len(title_card.find_all("h5")) > 1 else None
        npm_el = title_card.find("h6")
        npm_match = re.search(r"[\d]{6,}", npm_el.get_text()) if npm_el else None
        identitas = {
            "periode": heading.get_text(strip=True) if heading else "-",
            "nama": nama_el.get_text(strip=True) if nama_el else "-",
            "npm": npm_match.group() if npm_match else "-"
        }

    siku_data, akademik_data = {}, {"mata_kuliah": [], "ip_semester": "-"}
    for card_body in soup_nilai.select(".main-card .card-body"):
        title_el = card_body.find("h5", class_="text-primary")
        if not title_el: continue
        title_text = title_el.get_text(strip=True).upper()
        
        if "NILAI KARAKTER" in title_text:
            table = card_body.find("table")
            if table and table.find("tbody"):
                cols = [c.get_text(strip=True) for c in table.find("tbody").find("tr").find_all("td")]
                if len(cols) >= 6:
                    siku_data = {"sikap": cols[0], "kehadiran": cols[1], "tugas": cols[2], "skp": cols[3], "angka": cols[4], "huruf": cols[5]}
        
        elif "NILAI AKADEMIK" in title_text:
            table = card_body.find("table")
            if table and table.find("tbody"):
                for row in table.find("tbody").find_all("tr"):
                    cols = row.find_all("td")
                    if len(cols) == 9:
                        vals = [c.get_text(strip=True) for c in cols]
                        akademik_data["mata_kuliah"].append({
                            "mk": vals[0], "kel": vals[1], "sks": vals[2], "uts": vals[3], "uas": vals[4], 
                            "akt": vals[5], "angka": vals[6], "huruf": vals[7], "indeks": vals[8]
                        })
                    elif len(cols) == 1:
                        akademik_data["ip_semester"] = cols[0].get_text(strip=True)

    # --- SKPM Dashboard ---
    resp_dash = session.get(SKPM_DASHBOARD_URL)
    soup_dash = BeautifulSoup(resp_dash.text, "html.parser")
    skpm_dash = {"total_kegiatan": "0", "total_nilai": "0", "rekap": []}
    
    for card in soup_dash.select(".widget-content-wrapper"):
        left, right = card.select_one(".widget-content-left"), card.select_one(".widget-content-right .widget-numbers span")
        if left and right:
            label = (left.select_one(".widget-subheading") or left.select_one(".widget-heading")).get_text(strip=True)
            if "Kegiatan" in label: skpm_dash["total_kegiatan"] = right.get_text(strip=True)
            if "Nilai" in label: skpm_dash["total_nilai"] = right.get_text(strip=True)
            
    table_dash = soup_dash.select_one("#example1")
    if table_dash and table_dash.find("tbody"):
        for row in table_dash.find("tbody").find_all("tr"):
            cols = row.find_all("td")
            if len(cols) >= 3:
                skpm_dash["rekap"].append({"periode": cols[1].get_text(strip=True), "nilai": cols[2].get_text(strip=True)})

    # --- SKPM Kelola (Detail) ---
    resp_detail = session.get(SKPM_DATA_URL)
    soup_detail = BeautifulSoup(resp_detail.text, "html.parser")
    skpm_detail = []
    
    table_detail = soup_detail.select_one(".table_umum")
    if table_detail and table_detail.find("tbody"):
        for row in table_detail.find("tbody").find_all("tr"):
            cols = row.find_all("td")
            if len(cols) >= 6:
                status_el = cols[5].find("span")
                skpm_detail.append({
                    "lingkup": cols[1].get_text(strip=True), "kegiatan": cols[2].get_text(strip=True),
                    "bobot": cols[4].get_text(strip=True), "status": (status_el.get_text(strip=True) if status_el else cols[5].get_text(strip=True))
                })

    return {
        "identitas": identitas,
        "siku": siku_data,
        "akademik": akademik_data,
        "skpm_dash": skpm_dash,
        "skpm_detail": skpm_detail
    }

def hitung_skor_otomatis(tingkat: str) -> int:
    return {"Internasional": 100, "Nasional": 75, "Provinsi": 50, "Regional": 25, "Kampus": 10}.get(tingkat, 0)

# ==========================================
# 5. ENDPOINTS API MAPRES & INTEGRASI (SECURED)
# ==========================================

@app.post("/api/login")
def login_and_scrape(req: LoginRequest):
    # 1. Normalisasi Input (Hapus spasi tersembunyi & ubah ke huruf kecil)
    input_npm = req.npm.strip().lower()
    input_password = req.password.strip()

    # 2. LOGIN ADMIN (Menggunakan input yang sudah dinormalisasi)
    if input_npm == "admin" and input_password == "kelompoksatu":
        # Generate token JWT untuk Admin
        token = create_access_token({"sub": "admin", "role": "admin"})
        return {
            "status": "success", 
            "role": "admin", 
            "token": token, # Kirim token ke frontend
            "data": {"identitas": {"nama": "Administrator", "npm": "admin"}}
        }

    # 3. LOGIN MAHASISWA
    with requests.Session() as session:
        # Gunakan req.npm asli agar format NPM yang dikirim ke Portal STAN tidak berubah
        success, msg = login_portal(session, req.npm.strip(), req.password)
        
        if not success:
            raise HTTPException(status_code=401, detail=msg)
            
        try:
            data = scrape_data(session)
            
            # --- INTEGRASI DATABASE ACONT ---
            npm = data["identitas"].get("npm", "-")
            nama = data["identitas"].get("nama", "-")
            
            def to_float(val):
                try: return float(str(val).replace(",", ".").strip())
                except: return 0.0
                
            ipk_val = to_float(data["akademik"].get("ip_semester", "0"))
            siku_val = to_float(data.get("siku", {}).get("angka", "0"))
            skpm_val = to_float(data.get("skpm_dash", {}).get("total_nilai", "0"))

            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO mahasiswa_stats (npm, nama, ipk, siku, skpm, is_kandidat) 
                VALUES (?, ?, ?, ?, ?, 0)
                ON CONFLICT(npm) DO UPDATE SET 
                nama=excluded.nama, ipk=excluded.ipk, siku=excluded.siku, skpm=excluded.skpm
            ''', (npm, nama, ipk_val, siku_val, skpm_val))
            
            cursor.execute("SELECT is_kandidat FROM mahasiswa_stats WHERE npm = ?", (npm,))
            row = cursor.fetchone()
            data["is_kandidat"] = bool(row[0]) if row else False

            cursor.execute("INSERT INTO audit_log (aktor, aksi, detail) VALUES (?, 'Login', 'Akses portal sukses')", (npm,))
            conn.commit()
            conn.close()

            # Generate token JWT untuk Mahasiswa
            token = create_access_token({"sub": npm, "role": "mahasiswa"})

            return {
                "status": "success", 
                "role": "mahasiswa", 
                "token": token, # Kirim token ke frontend
                "data": data
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Gagal mengekstrak tabel data: {str(e)}")

@app.post("/api/daftar_kandidat")
def daftar_kandidat(req: DaftarKandidatRequest, current_user: dict = Depends(verify_token)):
    # OTORISASI: Pastikan mahasiswa tidak mendaftarkan NPM orang lain
    if current_user["role"] != "admin" and current_user["sub"] != req.npm:
        raise HTTPException(status_code=403, detail="Akses ditolak: Anda tidak bisa mendaftarkan NPM lain.")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE mahasiswa_stats SET is_kandidat = 1 WHERE npm = ?", (req.npm,))
    cursor.execute("INSERT INTO audit_log (aktor, aksi, detail) VALUES (?, 'Daftar Kandidat', 'Mendeklarasikan diri maju kandidat')", (req.npm,))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Selamat! Anda resmi terdaftar sebagai Kandidat Mapres."}

@app.post("/api/ajukan_mapres")
def ajukan_mapres(req: AjukanMapresRequest, current_user: dict = Depends(verify_token)):
    # OTORISASI: Pastikan mahasiswa tidak mengajukan prestasi menggunakan akun/NPM orang lain
    if current_user["role"] != "admin" and current_user["sub"] != req.npm:
        raise HTTPException(status_code=403, detail="Akses ditolak: Anda tidak bisa mengajukan prestasi untuk NPM lain.")

    if not cek_status_waktu_pengajuan():
        raise HTTPException(status_code=403, detail="Batas pengajuan ditutup (Maks tanggal terakhir jam 15.00 WIB).")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO mapres (npm, nama, nama_prestasi, kategori, tingkat, link_bukti) VALUES (?, ?, ?, ?, ?, ?)', 
                   (req.npm, req.nama, req.nama_prestasi, req.kategori, req.tingkat, req.link_bukti))
    cursor.execute("INSERT INTO audit_log (aktor, aksi, detail) VALUES (?, 'Ajukan Prestasi', ?)", (req.npm, f"Mengajukan: {req.nama_prestasi}"))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Prestasi diajukan dan masuk antrean verifikasi Admin."}

@app.get("/api/status_pengajuan_saya")
def lihat_status_pengajuan(npm: str, current_user: dict = Depends(verify_token)):
    # OTORISASI: Cegah mahasiswa mengintip status pengajuan mahasiswa lain (Admin bebas)
    if current_user["role"] != "admin" and current_user["sub"] != npm:
        raise HTTPException(status_code=403, detail="Akses ditolak: Anda hanya dapat melihat data Anda sendiri.")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT nama_prestasi, tingkat, status, skor, alasan_tolak FROM mapres WHERE npm = ? ORDER BY id DESC", (npm,))
    hasil = [{"prestasi": r[0], "tingkat": r[1], "status": r[2], "skor": r[3], "alasan": r[4]} for r in cursor.fetchall()]
    conn.close()
    return {"status": "success", "data": hasil}

@app.get("/api/pengajuan_pending")
def lihat_pengajuan_pending(current_user: dict = Depends(verify_token)):
    # OTORISASI KHUSUS ADMIN
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Hanya Administrator yang memiliki akses ke halaman ini.")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, npm, nama, nama_prestasi, kategori, tingkat, link_bukti FROM mapres WHERE status = 'Pending'")
    hasil = [{"id": r[0], "npm": r[1], "nama": r[2], "nama_prestasi": r[3], "kategori": r[4], "tingkat": r[5], "link_bukti": r[6]} for r in cursor.fetchall()]
    conn.close()
    return {"status": "success", "data": hasil}

@app.post("/api/approve_mapres")
def verifikasi_mapres(req: VerifikasiMapresRequest, current_user: dict = Depends(verify_token)):
    # OTORISASI KHUSUS ADMIN
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Hanya Administrator yang dapat memverifikasi prestasi.")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    if req.keputusan.lower() == "disetujui":
        cursor.execute("SELECT tingkat, nama_prestasi FROM mapres WHERE id = ?", (req.id_pengajuan,))
        row = cursor.fetchone()
        skor = hitung_skor_otomatis(row[0])
        
        cursor.execute("UPDATE mapres SET status = 'Disetujui', skor = ?, alasan_tolak = '-' WHERE id = ?", (skor, req.id_pengajuan))
        cursor.execute("INSERT INTO audit_log (aktor, aksi, detail) VALUES ('Admin', 'ACC Mapres', ?)", (f"Menyetujui {row[1]} (+{skor} poin)",))
        pesan = f"Disetujui. +{skor} poin."
    else:
        cursor.execute("SELECT nama_prestasi FROM mapres WHERE id = ?", (req.id_pengajuan,))
        nama_pres = cursor.fetchone()[0]
        
        cursor.execute("UPDATE mapres SET status = 'Ditolak', skor = 0, alasan_tolak = ? WHERE id = ?", (req.alasan, req.id_pengajuan))
        cursor.execute("INSERT INTO audit_log (aktor, aksi, detail) VALUES ('Admin', 'Tolak Mapres', ?)", (f"Menolak {nama_pres}. Alasan: {req.alasan}",))
        pesan = "Pengajuan ditolak dengan alasan tersimpan."
        
    conn.commit()
    conn.close()
    return {"status": "success", "message": pesan}

@app.get("/api/ranking")
def get_ranking_mapres(current_user: dict = Depends(verify_token)):
    # Memastikan hanya user login (mahasiswa atau admin) yang bisa melihat tabel ranking
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT m.npm, m.nama, m.ipk, m.siku, m.skpm, COALESCE(SUM(p.skor), 0) as skor_prestasi
        FROM mahasiswa_stats m
        LEFT JOIN mapres p ON m.npm = p.npm AND p.status = 'Disetujui'
        WHERE m.is_kandidat = 1
        GROUP BY m.npm, m.nama, m.ipk, m.siku, m.skpm
    ''')
    rows = cursor.fetchall()
    conn.close()
    
    ranking = []
    for r in rows:
        npm, nama, ipk, siku, skpm, skor_prestasi = r
        skor_akhir = (ipk * 20) + (siku * 0.5) + skpm + skor_prestasi
        ranking.append({
            "npm": npm, "nama": nama, "ipk": ipk, "siku": siku, "skpm": skpm,
            "skor_prestasi": skor_prestasi, "total_skor": round(skor_akhir, 2)
        })
    ranking.sort(key=lambda x: x["total_skor"], reverse=True)
    for i, item in enumerate(ranking): item["peringkat"] = i + 1
    return {"status": "success", "data": ranking}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
