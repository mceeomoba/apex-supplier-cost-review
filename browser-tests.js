/* Synthetic parser and money regressions. Run: node browser-tests.js */
require('./browser-review.js');const assert=require('node:assert/strict');const a=ApexReview;
const c='SKU,Price,Cost per item\n001,20,8\nD,20,8\nD,20,8';
let r=a.run(c,'SKU,Cost\n001,12\n1,12\nD,3');
assert.equal(r.results[0].newProductMarginPercent,'40.00');assert.equal(r.results[1].status,'REVIEW');assert.equal(r.results[2].status,'REVIEW');
assert.equal(a.run(c,'SKU,Cost\n').catalogFlags.length,1);
r=a.run(c,'SKU,Cost\n,\n001,12\n');assert.equal(r.results[0].status,'REVIEW');assert.equal(r.results[0].supplierRow,2);assert.equal(r.results[1].supplierRow,3);
assert.throws(()=>a.run(c,'SKU,Cost\n,,,\n001,12\n'),/Ragged/);
r=a.run(c,'SKU,Cost\n\n001,12\n');assert.equal(r.results.length,1);assert.equal(r.results[0].supplierRow,3);
r=a.run(c,'SKU,Cost\n"multi\nline",2\n001,12\n');assert.equal(r.results[0].sku,'multi\nline');assert.equal(r.results[1].supplierRow,4);
for(const bad of ['SKU,Cost\n001,1,2','SKU,SKU\n001,2','SKU,Cost\n"001,2'])assert.throws(()=>a.run(c,bad));
for(const v of ['','-1','1e2','"1,200"','99999999999999999'])assert.equal(a.run(c,'SKU,Cost\n001,'+v+'\n').results[0].status,'REVIEW');
assert.equal(a.run('SKU,Price,Cost per item\n,20,8\n','SKU,Cost\n').catalogFlags.length,1);
console.log('PASS: browser synthetic regressions, including empty-field records and physical line positions.');
