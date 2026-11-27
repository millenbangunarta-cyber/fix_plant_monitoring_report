# FIX PLANT MONITORING REPORT
## PT EQUALINDO MAKMUR ALAM SEJAHTERA

CMMS web application untuk monitoring maintenance empat plant:
- BLC
- CPP BANGLADESH
- CPP JEPANG BESAR
- CPP JEPANG KECIL

### Modul
Dashboard terpusat, Plant Monitoring, Equipment Database, Work Order/Breakdown, Preventive Maintenance, Inventory dengan transaksi IN/OUT, Supplier, Activity Log, Maintenance Analytics, dan export Work Order PDF.

### Deploy ke Render.com
1. Ekstrak ZIP.
2. Upload isi folder `fix_plant_monitoring_report` ke repository GitHub.
3. Di Render pilih **New + > Blueprint** dan hubungkan repository.
4. Render membaca `render.yaml`, lalu menyiapkan Web Service dan PostgreSQL.
5. Isi environment variables `ADMIN_USERNAME` dan `ADMIN_PASSWORD` di Render.
6. Deploy dan buka URL `.onrender.com` yang diberikan Render.

### Login
Username dan password ditentukan sendiri melalui environment variables Render:
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`

Tidak ada akun default produksi. Jika menjalankan lokal tanpa mengatur environment, username `admin` dan password `ChangeMe123!` digunakan hanya untuk uji coba lokal.

### Jalankan lokal
Python 3.11+:
```bash
pip install -r requirements.txt
python app.py
```
Buka `http://127.0.0.1:5000`.

### Catatan sebelum operasional
Ini adalah starter/MVP. Lakukan uji coba dan backup sebelum penggunaan resmi. Render Free web service dapat sleep saat tidak aktif, dan ketentuan retensi database gratis dapat berubah; untuk data maintenance produksi gunakan database dengan backup dan retensi yang sesuai. Versi ini belum memiliki multi-user role, approval workflow, edit/delete UI, file/photo attachments, QR code, maupun notifikasi otomatis.
