# Apex Supplier Cost Review

A read-only tool for a narrow merchant task: compare a supplier's new unit costs against a current catalog and see which exact SKU matches would reduce product margin. No Shopify login, installation into your store, or data upload.

This is an early, free prototype from Apex, an AI-assisted software project. It is not a Shopify app, affiliated with Shopify, or a paid service. No customer results or sales claimed.

## Run locally

Requires Python 3.9 or later. No third-party packages.

```
python3 review.py --self-test
python3 review.py --demo
python3 review.py --catalog catalog.csv --supplier supplier.csv > review.json
```

Catalog headers: `SKU,Price,Cost per item`. Supplier headers: `SKU,Cost`. For older Shopify exports, use `--sku "Variant SKU" --price "Variant Price"`. Other header names can be set with `--old-cost`, `--supplier-sku` and `--new-cost`.

Save output to a different path, never either input. Shell redirection can truncate a file before the program starts.

Use CSV files copied directly from their source, encoded as UTF-8. Keep the originals. The tool treats identifiers as text and matches exact case, including leading zeros. It does not repair identifiers already damaged by a spreadsheet.

## What you get

A JSON review with supplier row numbers, exact SKUs, cost changes, and old/new product margin percentages. Synthetic example: selling price 20, old unit cost 8, new unit cost 12 produces a cost increase of 4 and product margin changing from 60% to 40%.

Duplicate catalog or supplier SKUs, unmatched identifiers, surrounding whitespace, blank or malformed amounts and zero selling prices are held for review. No arbitrary first match, fuzzy matching or silent zeroing. Blank catalog SKUs and duplicate groups are counted separately. Exit code 1 means a supplier row or a catalog SKU group needs review, not a program crash; 2 means rejected input.

## Boundaries

Both files must use the same currency and unit-cost basis. The tool does not detect currency mismatch. Product margin is `(selling price - unit cost) / selling price`; it excludes shipping, payment fees, tax, discounts, returns and overhead. It is not net profit or financial advice.

The output is **not a Shopify import file**. Nothing is written to either source file or to a store. Do not import the report. Confirm matches and costs with your supplier and in Shopify before making any separate changes. Supplier items missing from the catalog are not added. Catalog items absent from the supplier file are not treated as zero stock or discontinued.

Processing uses Python's standard library locally. The code contains no network calls. Keep reports private: they may contain confidential SKUs and costs. Maximum input size is 10 MB per file. CSV only, not XLSX. Extremely large numeric values that exceed decimal precision are rejected as a whole input rather than returning a partial report.

## Evidence and alternatives

A merchant [described the difficulty of mapping supplier SKU-only spreadsheets to Shopify exports](https://community.shopify.com/t/update-shopify-stock-levels-via-csv-with-no-handle-only-sku/306346). That is evidence of inventory SKU-mapping friction only, not proven demand for supplier-cost or margin review and not proof anyone will pay for this tool.

Shopify's [current CSV documentation](https://help.shopify.com/en/manual/products/import-export/using-csv) describes product identifiers, prices and related-column risks. This utility avoids generating an import altogether.

There are existing solutions, including [SupplierSafe](https://apps.shopify.com/suppliersafe), bulk-editing apps and spreadsheet lookups. This is not claimed to be an uncrowded market. Apex's first piece is deliberately narrower: a local, exact-match supplier-cost review without modifying store data.

## Verification

Version 0.1.0 passes 17 synthetic checks, including leading zeros, ambiguous SKUs, case mismatch, malformed monetary amounts, duplicate headers and ragged CSV. No real merchant file or live Shopify store has been tested. Run `--self-test` yourself before trying copies of your files.
