/* Apex supplier-cost review. Local-only. No network or store writes. */
(function(root){
'use strict';
function csv(text){
 const rows=[],lines=[];let row=[],cell='',quoted=false,closed=false,hasContent=false,line=1,startLine=1;
 text=text.replace(/^\uFEFF/,'');
 function finish(){row.push(cell);if(hasContent){rows.push(row);lines.push(startLine);}row=[];cell='';closed=false;hasContent=false;}
 for(let i=0;i<text.length;i++){
  const c=text[i];
  if(quoted){if(c==='"'){if(text[i+1]==='"'){cell+='"';i++;}else{quoted=false;closed=true;}}else{cell+=c;if(c==='\n')line++;else if(c==='\r'&&text[i+1]!=='\n')line++;}continue;}
  if(c==='"'){if(cell||closed)throw Error('Unexpected quote in CSV');quoted=true;hasContent=true;continue;}
  if(c===','){row.push(cell);cell='';closed=false;hasContent=true;continue;}
  if(c==='\n'||c==='\r'){finish();if(c==='\r'&&text[i+1]==='\n')i++;line++;startLine=line;continue;}
  if(closed)throw Error('Unexpected characters after quoted field');cell+=c;hasContent=true;
 }
 if(quoted)throw Error('Unclosed CSV quote');
 if(hasContent)finish();
 if(!rows.length)throw Error('CSV is empty');
 const h=rows.shift();lines.shift();if(new Set(h).size!==h.length)throw Error('Duplicate headers');
 if(rows.some(r=>r.length!==h.length))throw Error('Ragged CSV row');
 return {headers:h,rows:rows.map(r=>Object.fromEntries(h.map((k,i)=>[k,r[i]]))),lines};
}
function money(s){if(!/^\d{1,16}(?:\.\d{1,4})?$/.test(s))throw Error('Use nonnegative decimals, at most 16 integer and 4 decimal digits; no currency, commas or exponent');const [a,b='']=s.split('.');return BigInt(a)*10000n+BigInt(b.padEnd(4,'0'));}
function number(n){const negative=n<0n;if(negative)n=-n;return (negative?'-':'')+(n/10000n).toString()+'.'+(n%10000n).toString().padStart(4,'0');}
function percent(price,cost){const n=(price-cost)*10000n;const v=n<0n?-((-n+price/2n)/price):(n+price/2n)/price;return(v<0n?'-':'')+(v<0n?-v:v)/100n+'.'+((v<0n?-v:v)%100n).toString().padStart(2,'0');}
function run(c,s){
 const cat=csv(c),sup=csv(s);
 for(const k of ['SKU','Price','Cost per item'])if(!cat.headers.includes(k))throw Error('Catalog needs SKU, Price, Cost per item headers');
 for(const k of ['SKU','Cost'])if(!sup.headers.includes(k))throw Error('Supplier needs SKU, Cost headers');
 const cm=new Map(),sm=new Map();
 for(const r of cat.rows){const a=cm.get(r.SKU)||[];a.push(r);cm.set(r.SKU,a);}
 for(const r of sup.rows)sm.set(r.SKU,(sm.get(r.SKU)||0)+1);
 const catalogFlags=[...cm].filter(([k,v])=>!k||k.trim()!==k||v.length>1).map(([k,v])=>({sku:k,rows:v.length,reason:!k?'Blank catalog SKU':k.trim()!==k?'Catalog SKU whitespace':'Duplicate catalog SKU'}));
 const results=sup.rows.map((r,i)=>{
  const out={supplierRow:sup.lines[i],sku:r.SKU,status:'REVIEW'};
  try{
   if(!r.SKU||r.SKU.trim()!==r.SKU)throw Error('Blank SKU or surrounding whitespace');
   if(sm.get(r.SKU)>1)throw Error('Duplicate supplier SKU');
   const matches=cm.get(r.SKU);if(!matches)throw Error('No exact catalog match');if(matches.length!==1)throw Error('Duplicate catalog SKU');
   const price=money(matches[0].Price),old=money(matches[0]['Cost per item']),next=money(r.Cost);if(price===0n)throw Error('Zero selling price');
   Object.assign(out,{status:'MATCHED_REVIEW_ONLY',sellingPrice:number(price),oldCost:number(old),newCost:number(next),costChange:number(next-old),oldProductMarginPercent:percent(price,old),newProductMarginPercent:percent(price,next),reason:'Review only; not a Shopify import'});
  }catch(e){out.reason=e.message;}return out;
 });
 return {version:'browser-0.1',catalogRows:cat.rows.length,supplierRows:sup.rows.length,catalogFlags,results,scope:'Same currency and unit basis assumed. Excludes fees, shipping, taxes, discounts, returns and overhead. Not profit or an import file.'};
}
root.ApexReview={csv,run};
})(typeof globalThis!=='undefined'?globalThis:this);
