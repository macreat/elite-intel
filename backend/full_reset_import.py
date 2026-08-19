#!/usr/bin/env python3
"""Full reset: wipe, create catalog, import kardex August CSV."""
import csv, hashlib, io, json, re, sys
from decimal import Decimal, InvalidOperation
import openpyxl, psycopg

DB_URL = "postgresql://postgres:postgres@elite_postgres:5432/elite_db"
CSV_PATH = "/app/data/kardex_august.csv"
XLSX_PATH = "/app/data/kardex_full.xlsx"
AMOUNT_RE = re.compile(r"[-+]?\d[\d.\s,]*\d|[-+]?\d")
SKIP_COLS = {"pendientes", "total"}

def parse_amount(text):
    if not text or not str(text).strip(): return None
    match = AMOUNT_RE.search(str(text))
    if not match: return None
    raw = match.group().strip()
    if not raw: return None
    sign, unsigned = ("", raw)
    if raw[0] in "+-": sign, unsigned = raw[0], raw[1:]
    if not unsigned or not any(c.isdigit() for c in unsigned): return None
    has_dot, has_comma = "." in unsigned, "," in unsigned
    if has_dot and has_comma:
        lp = max(unsigned.rfind("."), unsigned.rfind(","))
        ls = unsigned[lp]
        trail = len(unsigned) - lp - 1
        if 1 <= trail <= 2:
            normalized = (unsigned[:lp].replace(".","").replace(",","") + "." + unsigned[lp+1:]) if ls == "," else unsigned.replace(",","")
        else:
            normalized = unsigned.replace(".","").replace(",","")
    elif has_dot:
        lp = unsigned.rfind(".")
        frac = unsigned[lp+1:]
        normalized = unsigned.replace(".","") if len(frac)==3 else unsigned[:lp].replace(".","")+"."+frac
    elif has_comma:
        lp = unsigned.rfind(",")
        frac = unsigned[lp+1:]
        if len(frac)==3: normalized = unsigned.replace(",","")
        else: normalized = unsigned[:lp].replace(",","")+"."+frac
    else:
        normalized = unsigned
    try: v = Decimal(sign + normalized)
    except InvalidOperation: return None
    if v <= 0: return None
    return v.quantize(Decimal("0.01"))

def source_fp(ch, rn): return hashlib.sha256(f"{ch}:{rn}".encode()).hexdigest()
def record_fp(at, tt, ci, d, a, cu, pi=None):
    return hashlib.sha256(json.dumps({"occurred_at":at,"transaction_type":tt,"category_id":ci,"description":d,"amount":str(a),"currency_code":cu,"product_id":pi},sort_keys=True).encode()).hexdigest()

def classify(h):
    h = h.lower().strip()
    if not h or h in SKIP_COLS: return None
    if "ahorro" in h and "pagar" in h: return ("Ahorro para pagar","EXPENSE")
    if h in ("salida","salidas"): return ("Salidas","EXPENSE")
    if "movil" in h: return ("Be Movil","INCOME")
    if "tigo" in h: return ("Tigo","INCOME")
    if "fotocopi" in h: return ("Fotocopias","INCOME")
    if "impresion" in h: return ("Impresiones","INCOME")
    if "scan" in h or "escaneo" in h: return ("Escaneo","INCOME")
    if "papeler" in h: return ("Papelería","INCOME")
    if "accesorio" in h: return ("Accesorios","INCOME")
    if "internet" in h: return ("Internet","INCOME")
    if "ahorro mensual" in h or h == "ahorro": return ("Ahorro mensual","INCOME")
    if h.replace(".","").replace(",","").isdigit(): return None
    return ("Otros","INCOME")

def parse_date(raw):
    raw = str(raw).strip()
    for fmt in ("%m/%d/%Y","%m/%d/%y","%d/%m/%Y"):
        try: return __import__("datetime").datetime.strptime(raw, fmt)
        except ValueError: continue
    return None

def main():
    conn = psycopg.connect(DB_URL)
    cur = conn.cursor()

    print("=== WIPING ===")
    cur.execute("DELETE FROM transactions")
    cur.execute("DELETE FROM import_rows")
    cur.execute("DELETE FROM import_batches")
    cur.execute("DELETE FROM products")
    cur.execute("DELETE FROM categories")
    conn.commit()

    print("=== CATEGORIES ===")
    cats = [
        ("Ahorro mensual","INCOME"),("Be Movil","INCOME"),("Tigo","INCOME"),
        ("Fotocopias","INCOME"),("Impresiones","INCOME"),("Escaneo","INCOME"),
        ("Papelería","INCOME"),("Accesorios","INCOME"),("Internet","INCOME"),
        ("Otros","INCOME"),("Recargas","INCOME"),("Servicios digitales","INCOME"),
        ("Salidas","EXPENSE"),("Ahorro para pagar","EXPENSE"),
    ]
    cat_ids = {}
    for name, tx_type in cats:
        cur.execute("INSERT INTO categories (name,type,active,created_at,updated_at) VALUES (%s,%s,true,NOW(),NOW()) RETURNING id",(name,tx_type))
        cat_ids[(name.lower(),tx_type)] = cur.fetchone()[0]
    conn.commit()
    print(f"  {len(cats)} categories created")

    print("=== PRODUCTS ===")
    wb = openpyxl.load_workbook(XLSX_PATH, read_only=True, data_only=True)
    ws = wb["Hoja2"]
    pc = 0
    for row in ws.iter_rows(min_row=3, values_only=True):
        name = str(row[0]).strip() if row[0] else ""
        if not name or name == "None": continue
        def cp(v):
            if v is None: return None
            m = re.search(r"[\d.]+", str(v).strip())
            if m:
                try: return Decimal(m.group())
                except: return None
            return None
        cur.execute("INSERT INTO products (name,invoice_price,local_price,currency_code,created_at,updated_at) VALUES (%s,%s,%s,'COP',NOW(),NOW())",(name,cp(row[1]) if len(row)>1 else None,cp(row[2]) if len(row)>2 else None))
        pc += 1
    wb.close()
    conn.commit()
    print(f"  {pc} products created")

    print("=== TRANSACTIONS ===")
    ch = hashlib.sha256(b"kardex_august_2026").hexdigest()
    inserted = skipped = errors = 0
    current_header = current_date = None
    batch = []

    with open(CSV_PATH, "r", encoding="latin-1") as f:
        for csv_line, line in enumerate(f):
            line = line.strip()
            if not line: continue
            row = list(csv.reader(io.StringIO(line)))[0]
            col0 = row[0].strip() if row[0] else ""

            if col0.lower() in ("ahorro mensual","ahorro"):
                current_header = [c.strip() for c in row]
                continue
            if "/" in col0 and len(col0) <= 12:
                dt = parse_date(col0)
                if dt: current_date = dt
                continue
            if not current_header or not current_date:
                skipped += 1
                continue

            occurred_at = current_date.strftime("%Y-%m-%dT00:00:00-05:00")

            for ci in range(1, min(len(row), len(current_header))):
                hdr = current_header[ci]
                res = classify(hdr)
                if res is None: continue
                cat_name, tx_type = res
                cat_id = cat_ids.get((cat_name.lower(), tx_type))
                if cat_id is None: continue
                raw_val = row[ci].strip() if ci < len(row) else ""
                if not raw_val: continue

                amounts = []
                for m in AMOUNT_RE.finditer(raw_val):
                    parsed = parse_amount(m.group().strip())
                    if parsed and parsed > 0: amounts.append(parsed)
                if not amounts:
                    skipped += 1
                    continue

                for amount in amounts:
                    fp = source_fp(ch, f"{csv_line}:{ci}:{amount}")
                    rec = record_fp(occurred_at, tx_type, cat_id, raw_val, str(amount), "COP")
                    batch.append((occurred_at, tx_type, cat_id, raw_val, str(amount), csv_line, rec, fp))

            # Flush batch every 500 rows
            if len(batch) >= 500:
                for b in batch:
                    try:
                        cur.execute(
                            "INSERT INTO transactions (occurred_at,transaction_type,category_id,description,amount,currency_code,source_type,import_batch_id,source_row_number,record_fingerprint,source_fingerprint,created_at,updated_at) VALUES (%s,%s,%s,%s,%s,'COP','CSV',NULL,%s,%s,%s,NOW(),NOW()) ON CONFLICT DO NOTHING",
                            b)
                        if cur.rowcount > 0: inserted += 1
                        else: skipped += 1
                    except Exception as e:
                        errors += 1
                conn.commit()
                batch = []
                print(f"  ... {inserted} inserted so far (line {csv_line})")

    # Flush remaining
    for b in batch:
        try:
            cur.execute(
                "INSERT INTO transactions (occurred_at,transaction_type,category_id,description,amount,currency_code,source_type,import_batch_id,source_row_number,record_fingerprint,source_fingerprint,created_at,updated_at) VALUES (%s,%s,%s,%s,%s,'COP','CSV',NULL,%s,%s,%s,NOW(),NOW()) ON CONFLICT DO NOTHING",
                b)
            if cur.rowcount > 0: inserted += 1
            else: skipped += 1
        except Exception as e:
            errors += 1
    conn.commit()

    print(f"\n=== RESULTS ===")
    print(f"  Inserted: {inserted}, Skipped: {skipped}, Errors: {errors}")

    print("\n=== VERIFICATION ===")
    cur.execute("SELECT transaction_type, COUNT(*), SUM(amount) FROM transactions GROUP BY transaction_type ORDER BY transaction_type")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]} txs, {row[2]} COP")
    cur.execute("SELECT COUNT(*) FROM products")
    print(f"  Products: {cur.fetchone()[0]}")
    conn.close()
    print("\nDone.")

if __name__ == "__main__":
    main()
