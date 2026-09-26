"""Generates the bundled SAMPLE label images (demo data) and their ground-truth text."""
import hashlib, json, os, random, textwrap
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "sample_labels")
F = "/usr/share/fonts/truetype/dejavu/"
bold = lambda s: ImageFont.truetype(F + "DejaVuSans-Bold.ttf", s)
reg = lambda s: ImageFont.truetype(F + "DejaVuSans.ttf", s)

LABELS = {
 "chococrunch_biscuits": {
   "title": "SAMPLE LABEL - CHOCOCRUNCH BISCUITS",
   "ingredients": "Wheat flour, Milk solids, Sugar, Cocoa, Peanut traces, Soy lecithin.",
   "allergen": "ALLERGEN INFORMATION: Contains wheat, milk, soy. May contain tree nuts.",
   "rows": [("Energy (kcal)", "480", "144"), ("Protein (g)", "6.5", "2.0"), ("Carbohydrate (g)", "68", "20.4"),
            ("Total Sugars (g)", "30", "9.0"), ("Dietary Fibre (g)", "2.0", "0.6"), ("Total Fat (g)", "20", "6.0"),
            ("Sodium (mg)", "400", "120")],
   "serving": "30 g"},
 "masala_noodles": {
   "title": "SAMPLE LABEL - QUICK MASALA NOODLES",
   "ingredients": "Refined wheat flour (Maida), Palm oil, Iodised salt, Wheat gluten, Thickener (508), Mixed spices, Onion powder, Garlic powder, Sugar, Flavour enhancer (627, 631), Asafoetida.",
   "allergen": "ALLERGEN INFORMATION: Contains wheat. Made in a facility that also processes milk.",
   "rows": [("Energy (kcal)", "443", "310"), ("Protein (g)", "9.3", "6.5"), ("Carbohydrate (g)", "64", "45"),
            ("Total Sugars (g)", "4.3", "3.0"), ("Dietary Fibre (g)", "2.9", "2.0"), ("Total Fat (g)", "17", "12"),
            ("Sodium (mg)", "1271", "890")],
   "serving": "70 g"},
 "roasted_makhana": {
   "title": "SAMPLE LABEL - ROASTED MAKHANA PEPPER",
   "ingredients": "Fox nuts (Makhana) 92%, Rice bran oil, Rock salt, Black pepper.",
   "allergen": "ALLERGEN INFORMATION: No major allergens used in this product.",
   "rows": [("Energy (kcal)", "350", "105"), ("Protein (g)", "11.7", "3.5"), ("Carbohydrate (g)", "60", "18"),
            ("Total Sugars (g)", "1.7", "0.5"), ("Dietary Fibre (g)", "6.7", "2.0"), ("Total Fat (g)", "5", "1.5"),
            ("Sodium (mg)", "200", "60")],
   "serving": "30 g"},
}


def text_of(L):
    lines = [L["title"], "INGREDIENTS: " + L["ingredients"], L["allergen"],
             f"NUTRITION INFORMATION Per 100 g Per serving ({L['serving']})"]
    lines += [f"{a} {b} {c}" for a, b, c in L["rows"]]
    return "\n".join(lines)


def render(key, L):
    W, H = 1100, 1250
    img = Image.new("RGB", (W, H), (250, 247, 240))
    d = ImageDraw.Draw(img)
    y = 50
    d.text((60, y), L["title"], font=bold(34), fill=(20, 20, 20)); y += 70
    d.line((60, y, W - 60, y), fill=(20, 20, 20), width=4); y += 25
    body = "INGREDIENTS: " + L["ingredients"]
    for ln in textwrap.wrap(body, 52):
        d.text((60, y), ln, font=reg(30), fill=(25, 25, 25)); y += 42
    y += 15
    for ln in textwrap.wrap(L["allergen"], 55):
        d.text((60, y), ln, font=bold(28), fill=(25, 25, 25)); y += 40
    y += 30
    d.rectangle((60, y, W - 60, y + 140 + 56 * len(L["rows"])), outline=(20, 20, 20), width=4)
    d.text((80, y + 18), "NUTRITION INFORMATION", font=bold(30), fill=(20, 20, 20))
    y += 70
    d.text((520, y), "Per 100 g", font=bold(26), fill=(20, 20, 20))
    d.text((720, y), f"Per serving ({L['serving']})", font=bold(26), fill=(20, 20, 20)); y += 50
    for a, b, c in L["rows"]:
        d.line((80, y - 8, W - 80, y - 8), fill=(60, 60, 60), width=1)
        d.text((80, y), a, font=reg(28), fill=(20, 20, 20))
        d.text((540, y), b, font=reg(28), fill=(20, 20, 20))
        d.text((780, y), c, font=reg(28), fill=(20, 20, 20)); y += 56
    d.text((60, H - 60), "Demo sample label generated for SafeBite. Not a real product.", font=reg(22), fill=(90, 90, 90))
    # make it look like a phone photo: slight rotation + blur + JPEG
    random.seed(key)
    img = img.rotate(random.uniform(-1.5, 1.5), expand=True, fillcolor=(205, 200, 190)).filter(ImageFilter.GaussianBlur(0.6))
    path = os.path.join(OUT, key + ".jpg")
    img.save(path, "JPEG", quality=88)
    return path


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    index = {}
    for k, L in LABELS.items():
        p = render(k, L)
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()
        index[h] = {"key": k, "file": os.path.basename(p), "text": text_of(L)}
    json.dump(index, open(os.path.join(HERE, "sample_labels.json"), "w"), indent=1)
    print("wrote", len(index))
