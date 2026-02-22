import os
from PIL import Image, ImageDraw, ImageFont

cliparts = [
    ("train_station_ticket_counter.png", "Train Station", (231, 76, 60)),
    ("convenience_store_snack_aisle.png", "Convenience Store", (46, 204, 113)),
    ("restaurant_ordering_table.png", "Restaurant", (241, 196, 15)),
    ("hotel_reception_desk.png", "Hotel Reception", (52, 152, 219)),
    ("hospital_reception.png", "Hospital", (155, 89, 182)),
    ("default_conversation.png", "Conversing", (149, 165, 166))
]

os.makedirs("data/clipart", exist_ok=True)
width, height = 400, 300

for filename, text, color in cliparts:
    img = Image.new('RGB', (width, height), color=color)
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("Arial.ttf", 30)
    except IOError:
        font = ImageFont.load_default()
        
    text_bbox = d.textbbox((0, 0), text, font=font)
    text_w = text_bbox[2] - text_bbox[0]
    text_h = text_bbox[3] - text_bbox[1]
    
    d.text(((width - text_w) / 2, (height - text_h) / 2), text, fill=(255, 255, 255), font=font)
    img.save(f"data/clipart/{filename}")

print("Successfully generated clipart placeholders in data/clipart/")
