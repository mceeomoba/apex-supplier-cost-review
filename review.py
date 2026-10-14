#!/usr/bin/env python3
"""Read-only supplier cost change review. Python 3.9+, standard library only."""
import argparse, csv, io, json, re, sys
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path

VERSION = '0.1.0'

def amount(value):
    # Currency, thousands separators, exponent notation and negative costs need human review.
    if not re.fullmatch(r'\d+(?:\.\d{1,4})?', value):
        raise ValueError('Expected nonnegative decimal without currency or separators')
    return Decimal(value)

def load(text, required):
    reader = csv.DictReader(io.StringIO(text.lstrip('\ufeff')), strict=True)
    if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
        raise ValueError('Missing or duplicate headers')
    if not set(required).issubset(reader.fieldnames):
        raise ValueError('Missing columns: ' + ', '.join(sorted(set(required)-set(reader.fieldnames))))
    rows = list(reader)
    if any(None in r or any(v is None for v in r.values()) for r in rows):
        raise ValueError('Ragged CSV row')
    return rows

def review(catalog_text, supplier_text, sku='SKU', price='Price', old_cost='Cost per item', supplier_sku='SKU', new_cost='Cost'):
    catalog = load(catalog_text, [sku, price, old_cost])
    supplier = load(supplier_text, [supplier_sku, new_cost])
    cat_counts = Counter(r[sku] for r in catalog if r[sku])
    sup_counts = Counter(r[supplier_sku] for r in supplier if r[supplier_sku])
    lookup = {r[sku]:r for r in catalog if r[sku]}
    results=[]
    for n,row in enumerate(supplier,2):
        key=row[supplier_sku]
        result={'supplier_row':n,'sku':key,'status':'REVIEW','reason':''}
        results.append(result)
        if not key or key != key.strip():
            result['reason']='Blank SKU or surrounding whitespace; exact identifiers required'; continue
        if sup_counts[key]!=1:
            result['reason']='Duplicate supplier SKU; no guess made'; continue
        if cat_counts[key]>1:
            result['reason']='Duplicate catalog SKU; no guess made'; continue
        if key not in lookup:
            result['reason']='No exact catalog SKU match; leading zeros and case are preserved'; continue
        item=lookup[key]
        try:
            selling,old,new=amount(item[price]),amount(item[old_cost]),amount(row[new_cost])
        except ValueError as e:
            result['reason']=str(e); continue
        if selling == 0:
            result['reason']='Zero selling price; margin percentage undefined'; continue
        result.update(status='MATCHED_REVIEW_ONLY', reason='Human approval required; no import file generated', selling_price=str(selling),old_cost=str(old),new_cost=str(new),cost_change=str(new-old),old_product_margin_percent=str(((selling-old)/selling*100).quantize(Decimal('.01'))),new_product_margin_percent=str(((selling-new)/selling*100).quantize(Decimal('.01'))))
    return {'version':VERSION,'catalog_rows':len(catalog),'supplier_rows':len(supplier),'catalog_blank_sku_rows':sum(not r[sku] for r in catalog),'catalog_duplicate_skus':sorted(k for k,v in cat_counts.items() if v>1),'scope':'Exact SKU cost review only. Same currency assumed. Excludes fees, shipping, taxes, discounts and returns. Not profit or a Shopify import file.','results':results}

CATALOG='SKU,Price,Cost per item\n00123,20.00,8.00\nDUP,30,10\nDUP,40,12\nZERO,0,0\n'
SUPPLIER='SKU,Cost\n00123,12.00\n123,12\nDUP,11\nZERO,1\nMISSING,3\n'

def tests():
    x=review(CATALOG,SUPPLIER)
    assert x['results'][0]['new_product_margin_percent']=='40.00'
    assert x['results'][0]['cost_change']=='4.00'
    assert all(r['status']=='REVIEW' for r in x['results'][1:])
    assert review(CATALOG,'SKU,Cost\n00123,1\n00123,2\n')['results'][0]['status']=='REVIEW'
    assert review(CATALOG,'SKU,Cost\n00123,"1,200"\n')['results'][0]['status']=='REVIEW'
    assert review(CATALOG,'SKU,Cost\n00123,1e2\n')['results'][0]['status']=='REVIEW'
    assert review(CATALOG,'SKU,Cost\n00123,\n')['results'][0]['status']=='REVIEW'
    assert review(CATALOG,'SKU,Cost\n 00123,1\n')['results'][0]['status']=='REVIEW'
    assert review(CATALOG,'SKU,Cost\n00123,-1\n')['results'][0]['status']=='REVIEW'
    assert review(CATALOG.replace('00123','abc'),'SKU,Cost\nABC,1\n')['results'][0]['status']=='REVIEW'
    try: load('SKU,SKU\na,b\n',['SKU'])
    except ValueError: pass
    else: raise AssertionError('Duplicate header accepted')
    try: load('SKU,Cost\na,1,extra\n',['SKU','Cost'])
    except ValueError: pass
    else: raise AssertionError('Ragged row accepted')
    assert review('\ufeff'+CATALOG,SUPPLIER)['results'][0]['sku']=='00123'
    import subprocess, tempfile
    with tempfile.TemporaryDirectory() as folder:
        cat=Path(folder)/'catalog.csv'; sup=Path(folder)/'supplier.csv'
        sup.write_text('SKU,Cost\n',encoding='utf-8')
        for data in ['SKU,Price,Cost per item\n,20,5\n','SKU,Price,Cost per item\nD,20,5\nD,20,5\n']:
            cat.write_text(data,encoding='utf-8')
            assert subprocess.run([sys.executable,__file__,'--catalog',str(cat),'--supplier',str(sup)],capture_output=True).returncode==1
        cat.write_bytes(b'\xff')
        r=subprocess.run([sys.executable,__file__,'--catalog',str(cat),'--supplier',str(sup)],capture_output=True)
        assert r.returncode==2 and b'Traceback' not in r.stderr
        r=subprocess.run([sys.executable,__file__,'--catalog',str(cat)+'missing','--supplier',str(sup)],capture_output=True)
        assert r.returncode==2 and b'Traceback' not in r.stderr
    print('PASS: 17 synthetic checks. No real merchant files tested.')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--catalog',type=Path); p.add_argument('--supplier',type=Path)
    p.add_argument('--demo',action='store_true'); p.add_argument('--self-test',action='store_true')
    p.add_argument('--sku',default='SKU'); p.add_argument('--price',default='Price'); p.add_argument('--old-cost',default='Cost per item')
    p.add_argument('--supplier-sku',default='SKU'); p.add_argument('--new-cost',default='Cost')
    a=p.parse_args()
    if a.self_test: tests(); return
    if not a.demo and not (a.catalog and a.supplier): p.error('Use --demo or provide --catalog and --supplier')
    if a.demo: c,s=CATALOG,SUPPLIER
    else:
        try:
            for file in (a.catalog,a.supplier):
                if file.stat().st_size>10_000_000: p.error('Each file must be at most 10 MB')
            c,s=a.catalog.read_text(encoding='utf-8-sig'),a.supplier.read_text(encoding='utf-8-sig')
        except (OSError,UnicodeError):
            p.exit(2,'Input rejected: cannot read UTF-8 CSV files\n')
    try: result=review(c,s,a.sku,a.price,a.old_cost,a.supplier_sku,a.new_cost)
    except (ValueError,csv.Error,InvalidOperation) as e: p.exit(2,'Input rejected: '+str(e)+'\n')
    print(json.dumps(result,indent=2,ensure_ascii=True))
    sys.exit(1 if result['catalog_blank_sku_rows'] or result['catalog_duplicate_skus'] or any(r['status']=='REVIEW' for r in result['results']) else 0)

if __name__=='__main__': main()
