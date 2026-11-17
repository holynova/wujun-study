#!/usr/bin/env python3
"""Prepare visual review sheets; acceptance is explicit after the actual review."""
import argparse,fcntl,hashlib,json,pathlib,shutil,subprocess,tempfile
from build_slides import has_vector_overlay, render_overlay_page, find_tool, POPPLER_BIN
from optimize_slides import optimize_pdf
from PIL import Image,ImageDraw
from pypdf import PdfReader
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('code');p.add_argument('--accept',action='store_true');p.add_argument('--notes');p.add_argument('--file');a=p.parse_args()
 if a.accept:
  cycle_lock=(ROOT/'state/cycle.lock').open('w')
  try:fcntl.flock(cycle_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:raise SystemExit('Pause production or wait for the current acceptance before accepting another deck')
 sfile=ROOT/'state/production.json'
 source=pathlib.Path(a.file) if a.file else ROOT/'work/slides'/f'{a.code}-original.pdf';pdf=PdfReader(source)
 if a.accept and len(pdf.pages)!=15:raise SystemExit(f'Expected exactly 15 pages; got {len(pdf.pages)}. Review and regenerate; do not pad or truncate.')
 target=ROOT/'work/review'/a.code;target.mkdir(parents=True,exist_ok=True)
 for i,page in enumerate(pdf.pages,1):
  if has_vector_overlay(page):
   with tempfile.TemporaryDirectory() as temp:
    tool=find_tool(POPPLER_BIN,'pdftoppm')
    if not tool:raise SystemExit('Set PDFTOPPM_BIN for vector-aware review')
    frame=render_overlay_page(source,i,tool,temp,(round(float(page.mediabox.width)),round(float(page.mediabox.height))));frame.save(target/f'{i}.png')
  else:(target/f'{i}.png').write_bytes(page.images[0].data)
 # Three sheets, five readable full-width slides each; individual originals retained.
 for start in range(1,len(pdf.pages)+1,5):
  sheet=Image.new('RGB',(1000,5*590),'#e8e5dd');draw=ImageDraw.Draw(sheet)
  for row,n in enumerate(range(start,min(start+5,len(pdf.pages)+1))):
   im=Image.open(target/f'{n}.png').convert('RGB');im.thumbnail((980,550));sheet.paste(im,((1000-im.width)//2,row*590+25));draw.text((12,row*590+6),str(n),fill='black')
  sheet.save(target/f'sheet-{start}.jpg',quality=95)
 if a.accept:
  if not a.notes:raise SystemExit('Record the completed visual/source review in --notes')
  plan=json.loads((ROOT/'src/data/plan.json').read_text());ep=next(i+1 for i,t in enumerate(plan['roadmap']) if t[0]==a.code)
  publish=ROOT/'public/slides'/f'ep-{ep}.pdf';publish.parent.mkdir(exist_ok=True)
  shutil.copyfile(source,publish);shutil.copyfile(source,ROOT/'work/slides'/f'ep-{ep}-uncompressed.pdf')
  optimize_pdf(publish)
  if publish.stat().st_size>=25*1024*1024:raise SystemExit('Optimized PDF still exceeds static asset limit')
  with (ROOT/'state/runner.lock').open('w') as lock:
   fcntl.flock(lock,fcntl.LOCK_EX)
   s=json.loads(sfile.read_text());r=s['topics'][a.code]
   r.update(status='reviewed',review_notes=a.notes,review_sha256=hashlib.sha256(source.read_bytes()).hexdigest());tmp=sfile.with_suffix('.tmp');tmp.write_text(json.dumps(s,ensure_ascii=False,indent=2));tmp.replace(sfile)
  print('Accepted:',a.code)
 else:print('Review sheets:',target)
if __name__=='__main__':main()
