"""Generates static/logo.png (placeholder crest). Replace the PNG with the real school logo any time."""
import os

from PIL import Image, ImageDraw, ImageFont

S = 512
im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(im)
d.ellipse((8, 8, S - 8, S - 8), fill="#1e3a8a")
d.ellipse((40, 40, S - 40, S - 40), outline="#fbbf24", width=10)
try:
    big, small = ImageFont.truetype("arialbd.ttf", 190), ImageFont.truetype("arialbd.ttf", 44)
except OSError:
    big = small = ImageFont.load_default()
d.text((S / 2, S / 2 - 20), "CE", font=big, fill="#fbbf24", anchor="mm")
d.text((S / 2, S / 2 + 130), "EXCELLENCE", font=small, fill="white", anchor="mm")
im.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "logo.png"))
