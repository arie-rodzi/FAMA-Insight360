# FAMA Agrosedia Premium Dashboard

Sistem Streamlit untuk upload fail Excel gabungan dan menjana dashboard outcome bagi 5 kategori Agrosedia:

1. ABR
2. GBBS
3. Medan GBBS
4. Karavan Tani
5. Medan Food Truck

## Cara guna

```bash
pip install -r requirements.txt
streamlit run app.py
```

Kemudian upload fail Excel gabungan seperti `gabungan_sheet_ke_2_updated.xlsx`.

## Ciri utama

- Auto detect sheet berdasarkan nama kategori.
- KPI jumlah jualan, bilangan entiti/outlet, kategori aktif dan YoY terkini.
- Trend tahunan 2021–2025.
- Komposisi jualan mengikut kategori.
- Ranking negeri.
- Outcome R berbanding sasaran 15%.
- Top 20 outlet/usahawan.
- Senarai risiko/intervensi berdasarkan R bawah sasaran.
- Download data yang telah ditapis.

## Nota penting

Untuk ABR, kolum `Avg_Monthly_2021` hingga `Avg_Monthly_2025` akan diautomasikan kepada anggaran jualan tahunan dengan darab 12.
