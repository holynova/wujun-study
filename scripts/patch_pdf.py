#!/usr/bin/env python3
"""Apply reviewed vector text corrections; never alter the original PDF."""
import argparse,io,json,pathlib
from pypdf import PdfReader,PdfWriter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('patches');p.add_argument('output');a=p.parse_args()
if pathlib.Path(a.source).resolve()==pathlib.Path(a.output).resolve():raise SystemExit('Preserve the source original')
pdfmetrics.registerFont(TTFont('Heiti','/System/Library/Fonts/STHeiti Medium.ttc',subfontIndex=1))
reader=PdfReader(a.source);writer=PdfWriter(clone_from=a.source);patches=json.load(open(a.patches))
for n,page in enumerate(writer.pages,1):
 changes=[x for x in patches if x['page']==n]
 if changes:
  w,h=float(page.mediabox.width),float(page.mediabox.height);buf=io.BytesIO();c=canvas.Canvas(buf,pagesize=(w,h));c.scale(w/1376,h/768)
  for x in changes:
   x0,y0,x1,y1=x['rect'];c.setFillColor(HexColor(x['fill']));c.setStrokeColor(HexColor(x.get('border',x['fill'])));c.setLineWidth(1.5);c.roundRect(x0,768-y1,x1-x0,y1-y0,x.get('radius',0),fill=1,stroke=bool(x.get('border')))
   c.setFillColor(HexColor(x.get('color','#111111')));c.setFont('Heiti',x['size'])
   for i,line in enumerate(x['lines']):
    if pdfmetrics.stringWidth(line,'Heiti',x['size'])>x1-x0-2*x.get('padding',12):raise ValueError(f'Page {n}: text exceeds patch width')
    left=x0+(x1-x0-pdfmetrics.stringWidth(line,'Heiti',x['size']))/2 if x.get('align')=='center' else x0+x.get('padding',12)
    c.drawString(left,768-y0-x.get('top',8)-x['size']-i*x['leading'],line)
  c.save();buf.seek(0);page.merge_page(PdfReader(buf).pages[0])
writer.add_metadata({'/Title':'吴军专题学习 · 校对版','/Subject':'保留原始插画，局部中文与出处校对'})
writer.write(a.output)
assert len(PdfReader(a.output).pages)==len(reader.pages)
print('Patched',len({x['page'] for x in patches}),'pages; original preserved')
