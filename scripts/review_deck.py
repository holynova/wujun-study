#!/usr/bin/env python3
"""Prepare visual review sheets; acceptance is explicit after the actual review."""
import argparse,hashlib,json,pathlib,shutil,subprocess
from PIL import Image,ImageDraw
from pypdf import PdfReader
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('code');p.add_argument('--accept',action='store_true');p.add_argument('--notes');a=p.parse_args()
 sfile=ROOT/'state/production.json';s=json.loads(sfile.read_text());r=s['topics'][a.code]
 source=ROOT/'work/slides'/f'{a.code}-original.pdf';pdf=PdfReader(source)
 if len(pdf.pages)!=15:raise SystemExit(f'Expected exactly 15 pages; got {len(pdf.pages)}. Review and regenerate; do not pad or truncate.')
 target=ROOT/'work/review'/a.code;target.mkdir(parents=True,exist_ok=True)
 for i,page in enumerate(pdf.pages,1):
  if len(page.images)!=1:raise SystemExit('Non-raster page: inspect with vector-aware rendering before acceptance')
  (target/f'{i}.png').write_bytes(page.images[0].data)
 # Three sheets, five readable full-width slides each; individual originals retained.
 for start in [1,6,11]:
  sheet=Image.new('RGB',(1000,5*590),'#e8e5dd');draw=ImageDraw.Draw(sheet)
  for row,n in enumerate(range(start,start+5)):
   im=Image.open(target/f'{n}.png').convert('RGB');im.thumbnail((980,550));sheet.paste(im,((1000-im.width)//2,row*590+25));draw.text((12,row*590+6),str(n),fill='black')
  sheet.save(target/f'sheet-{start}.jpg',quality=95)
 if a.accept:
  if not a.notes:raise SystemExit('Record the completed visual/source review in --notes')
  plan=json.loads((ROOT/'src/data/plan.json').read_text());ep=next(i+1 for i,t in enumerate(plan['roadmap']) if t[0]==a.code)
  publish=ROOT/'public/slides'/f'ep-{ep}.pdf';publish.parent.mkdir(exist_ok=True)
  if source.stat().st_size>=25*1024*1024:raise SystemExit('PDF exceeds static asset limit; optimize before publishing')
  shutil.copyfile(source,publish);shutil.copyfile(source,ROOT/'work/slides'/f'ep-{ep}-uncompressed.pdf')
  r.update(status='reviewed',review_notes=a.notes,review_sha256=hashlib.sha256(source.read_bytes()).hexdigest());tmp=sfile.with_suffix('.tmp');tmp.write_text(json.dumps(s,ensure_ascii=False,indent=2));tmp.replace(sfile)
  print('Accepted:',a.code)
 else:print('Review sheets:',target)
if __name__=='__main__':main()
