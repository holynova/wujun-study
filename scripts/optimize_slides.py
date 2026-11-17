#!/usr/bin/env python3
"""Optimize PDF image encoding without resizing or flattening vector overlays."""
import io,pathlib,sys
from PIL import Image
from pypdf import PdfReader,PdfWriter

def optimize_pdf(source):
 source=pathlib.Path(source);before=source.stat().st_size;writer=PdfWriter(clone_from=source)
 for page in writer.pages:
  for image in list(page.images):
   with Image.open(io.BytesIO(image.data)) as original:
    # Re-encode only; keep the exact source pixels, page transform and vectors.
    rgb=original.convert('RGB');image.replace(rgb,quality=95,subsampling=0)
 writer.compress_identical_objects(remove_duplicates=True,remove_unreferenced=True)
 tmp=source.with_suffix('.optimized.pdf');writer.write(tmp)
 check=PdfReader(tmp);old=PdfReader(source)
 if len(check.pages)!=len(old.pages) or any(a.mediabox!=b.mediabox for a,b in zip(check.pages,old.pages)):
  tmp.unlink();raise RuntimeError('Optimization changed page count or geometry')
 if tmp.stat().st_size<before:tmp.replace(source)
 else:tmp.unlink()
 print(f'{source.name}: {before/1e6:.2f} -> {source.stat().st_size/1e6:.2f} MB')
if __name__=='__main__':optimize_pdf(sys.argv[1])
