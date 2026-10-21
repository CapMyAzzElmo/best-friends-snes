"""Lay out sprite sheet frames side by side, scaled up, for review."""
import sys
from PIL import Image
src, fw, fh, scale, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
im = Image.open(src).convert("RGBA")
pal = Image.open(src).getpalette()[:3]
n = im.height // fh
bg = Image.new("RGBA", (n * (fw + 4) * scale, fh * scale), (150, 170, 190, 255))
data = Image.open(src)
for i in range(n):
    f = im.crop((0, i * fh, fw, (i + 1) * fh))
    idx = data.crop((0, i * fh, fw, (i + 1) * fh))
    mask = Image.new("L", idx.size)
    mask.putdata([255 if v else 0 for v in idx.getdata()])
    f.putalpha(mask)
    f = f.resize((fw * scale, fh * scale), Image.NEAREST)
    bg.alpha_composite(f, (i * (fw + 4) * scale, 0))
bg.save(out)
