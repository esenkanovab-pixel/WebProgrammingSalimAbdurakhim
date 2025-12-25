from PIL import Image, ImageDraw, ImageFont
import os

out_dir = os.path.join('media', 'certificates', 'templates')
os.makedirs(out_dir, exist_ok=True)
path = os.path.join(out_dir, 'background.png')
img = Image.new('RGB', (1600, 1200), color=(245, 245, 230))
d = ImageDraw.Draw(img)
# Draw a border
d.rectangle([(10,10),(1589,1189)], outline=(180,180,180), width=6)
# Text
try:
    font = ImageFont.truetype('arial.ttf', 48)
except Exception:
    font = ImageFont.load_default()
d.text((80,80), 'Certificate Template', fill=(60,60,60), font=font)
img.save(path)
print('Created placeholder template at', path)