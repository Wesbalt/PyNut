# Nutritional data source: myfooddata.com, and their data is based on
# SR Legacy and FNDDS data. Download link:
# https://tools.myfooddata.com/nutrition-facts-database-spreadsheet.php

# To find the FDC ID of a food:
# Search for it on https://tools.myfooddata.com/nutrition-facts.php
# Follow the "data source" link at the bottom of the page.
# There is the FDC ID. Cool.

import sys, textwrap, math, os
from PIL import Image, ImageDraw, ImageFont
sys.stdout.reconfigure(encoding="utf-8")

sans48bold  = ImageFont.truetype(r"fonts/LiberationSans-Bold.ttf", 48)
sans96bold  = ImageFont.truetype(r"fonts/LiberationSans-Bold.ttf", 96)
sans128bold = ImageFont.truetype(r"fonts/LiberationSans-Bold.ttf", 128)
sans192bold = ImageFont.truetype(r"fonts/LiberationSans-Bold.ttf", 192)

# Source of DRVs (of adults):
# https://www.efsa.europa.eu/en/interactive-pages/drvs
EI = 2500 # kcal intake
# Vitamin (and choline) DRVs
# B1 and B3 values based on megajoule intake, hence the formulas.
drv_a   = 650 # mcg RE
drv_b1  = 0.1*EI/238.83 # mg, aka Thiamin
drv_b2  = 1.6 # mg, aka Riboflavin
drv_b3  = 1.6*EI/238.83 # mg NE, aka Niacin
drv_b5  = 5 # mg, aka Pantothenic acid
drv_b6  = 1.6 # mg
drv_b7  = 40 # mcg, aka Biotin
drv_b9  = 330 # mcg DFE, aka Folate
drv_b12 = 4 # mcg
drv_c   = 95 # mg
drv_d   = 15 # mcg
drv_e   = 11 # mg, aka Alpha-tocopherol
drv_k   = 70 # mcg, aka Phylloquinone
drv_choline = 400 # mg
# Mineral DRVs
drv_potassium  = 3500 # mg
drv_sodium     = 2000 # mg
drv_calcium    = 1000 # mg
drv_phosphorus = 550 # mg
drv_magnesium  = 300 # mg
drv_iron       = 16 # mg
drv_zinc       = 10.125 # mg, average of four PRIs depending on LPI
drv_manganese  = 3 # mg
drv_copper     = 1.3 # mg
drv_molybdenum = 65 # mcg
drv_selenium   = 70 # mcg
drv_chloride   = 3100 # mg
# Fatty acid DRVs
# Expressed as energy intake % in the DRV Finder, hence the formulas.
drv_omega_3 = 0.005*EI/9*1000 # mg, aka Alpha-Linolenic acid (ALA)
drv_omega_6 = 0.04 *EI/9*1000 # mg, aka Linoleic acid (LA)

class Food():
    pass

# Returns a list contains tuples (FDC ID, serving in grams, serving desc)
def read_foods(fname : str) -> [(int,int,str)]:
    f = open(fname, "r")
    lines = f.read().splitlines()
    foods_data = []

    def next_index() -> int:
        for i in range(len(lines)):
            line = lines[i]
            if len(line) == 0 or line.isspace() or line[0] == "#":
                continue
            else:
                return i
        return -1

    while True:
        # Read FDC ID
        i = next_index()
        if i == -1:
            break
        try:
            int(lines[i])
        except ValueError:
            print("Error on line %d: expected an FDC ID (int), got \"%s\"" % (i, lines[i]))
            return None
        fdc_id = int(lines[i])
        lines = lines[i+1:] # Discard the lines read in next_index()

        # Read serving size
        i = next_index()
        if i == -1:
            print("Reached EOF prematurely")
            return None
        try:
            int(lines[i])
        except ValueError:
            print("Error on line %d: expected a serving size (int), got \"%s\"" % (i, lines[i]))
            return None
        serving_size = int(lines[i])
        lines = lines[i+1:] # Discard the lines read in next_index()

        # Read serving description
        i = next_index()
        if i == -1:
            print("Reached EOF prematurely")
            break
        serving_desc = lines[i]
        lines = lines[i+1:] # Discard the lines read in next_index()

        # Store read data
        foods_data.append((fdc_id, serving_size, serving_desc))

    f.close()
    return foods_data

def get_nutrients(food_data : (int,int,str)) -> Food:
    fdc_id = int(food_data[0])
    items = []
    for entry in entries:
        items = entry.split(",")
        if str(fdc_id) == items[0]:
            break
    if str(fdc_id) != items[0]:
        print("Could not find FDC ID %s in the datasheet" % fdc_id)
        return None
    name = items[1]

    food              = Food()
    food.fdc_id       = fdc_id
    food.name         = str(items[1])
    food.serving_size = int(food_data[1])
    food.serving_desc = str(food_data[2])

    # Use this factor to make values reflect the serving
    factor = food.serving_size/100

    def read_value(i : int):
        # NULL in the datasheet means insignificant or unmeasured value.
        if items[i] == "NULL":
            items[i] = -sys.maxsize
        try:
            float(items[i])
        except ValueError:
            print("Non-float value at FDC ID %s index %d: %s" % (food.fdc_id, i, items[i]))
            sys.exit(1)
        return float(items[i]) * factor

    food.kcals          = read_value(3)  # kcalories
    food.fat            = read_value(4)  # g
    food.carbs          = read_value(6)  # g
    food.protein        = read_value(5)  # g
    food.fiber          = read_value(8)  # g
    food.sugars         = read_value(7)  # g
    food.water          = read_value(23) # g
    food.net_carbs      = read_value(22) # g
    food.sat_fats       = read_value(10) # g
    food.monounsat_fats = read_value(70) # mg
    food.polyunsat_fats = read_value(71) # mg
    food.cholesterol    = read_value(9)  # mg
    food.omega_3        = read_value(24) # mg
    food.omega_6        = read_value(25) # mg
    food.trans_fats     = read_value(27) # g
    food.vit_a   = read_value(16) # mcg RAE
    food.vit_b1  = read_value(47) # mg, aka Thiamin
    food.vit_b2  = read_value(48) # mg, aka Riboflavin
    food.vit_b3  = read_value(49) # mg, aka Niacin
    food.vit_b5  = read_value(50) # mg, aka Pantothenic acid
    food.vit_b6  = read_value(51) # mg
    food.vit_b7  = read_value(52) # mcg, aka Biotin
    food.vit_b9  = read_value(56) # mcg, aka Folate
    food.vit_b12 = read_value(18) # mcg
    food.vit_c   = read_value(17) # mg
    food.vit_d   = read_value(19) # mcg
    food.vit_e   = read_value(20) # mg, aka Alpha-tocopherol
    food.vit_k   = read_value(67) # mcg, aka Phylloquinone
    food.histidine     = read_value(87) # mg
    food.isoleucine    = read_value(78) # mg
    food.leucine       = read_value(79) # mg
    food.lysine        = read_value(80) # mg
    food.methionine    = read_value(81) # mg
    food.phenylalanine = read_value(83) # mg
    food.threonine     = read_value(77) # mg
    food.tryptophan    = read_value(76) # mg
    food.valine        = read_value(85) # mg
    food.potassium     = read_value(13) # mg
    food.sodium        = read_value(39) # mg
    food.calcium       = read_value(11) # mg
    food.phosphorus    = read_value(38) # mg
    food.magnesium     = read_value(14) # mg
    food.iron          = read_value(12) # mg
    food.zinc          = read_value(40) # mg
    food.manganese     = read_value(42) # mg
    food.copper        = read_value(41) # mg
    food.molybdenum    = read_value(45) # mcg
    food.selenium      = read_value(43) # mcg
    food.choline       = read_value(57) # mg
    food.chloride      = read_value(46) # mg

    # If fat is practically zero (<1 per 100 g),
    # obviously all subcategories are practically zero.
    # However, the datasheet makes these values NULL
    # instead of zero sometimes so let's fix that.
    if food.fat < 1:
        food.sat_fats       = 0
        food.monounsat_fats = 0
        food.polyunsat_fats = 0
        food.omega_3        = 0
        food.omega_6        = 0
        food.trans_fats     = 0
    if food.sugars < 0:
        food.sugars = 0

    # Test the assumption that we didn't find values of these.
    assert food.chloride < 0
    assert food.molybdenum < 0
    assert food.vit_b7 < 0

    return food

def draw_centered_circle(draw : ImageDraw.Draw, r : float, cx : float, cy : float, color, fill : bool, width : int = 1):
    if fill:
        draw.ellipse((cx-r, cy-r, cx+r, cy+r), fill=color)
    else:
        draw.ellipse((cx-r, cy-r, cx+r, cy+r), outline=color, width=width)

def draw_centered_text(draw : ImageDraw.Draw, text : str, cx : float, cy : float, font : ImageFont.ImageFont, color):
    w, h = draw.textsize(text, font=font)
    draw.text((cx-w/2, cy-h/2), text, fill=color, font=font, align="center")

def make_macros_bar(food : Food):
    legend = [
        ("Sat. fat",    "#d60270"),
        ("Poly. fat",   "#9b4f96"),
        ("Mono. fat",   "#0038a8"),
        ("Other fats",  "#12a6a5"),
        ("Fiber",       "#a9ae17"),
        ("Sugars",      "#4dad1c"),
        ("Other carbs", "#2b754c"),
        ("Protein",     "#d63c3c")
    ]
    img_width  = 1024
    img_height = 2048
    img = Image.new("RGB", (img_width, img_height), "white")
    draw = ImageDraw.Draw(img)

    # These are all the macros to be shown
    other_fats = food.fat - food.sat_fats - food.polyunsat_fats/1000 - food.monounsat_fats/1000
    other_carbs = food.carbs - food.fiber - food.sugars
    macros = [
        food.sat_fats,
        food.polyunsat_fats/1000,
        food.monounsat_fats/1000,
        other_fats,
        food.fiber,
        food.sugars,
        other_carbs,
        food.protein,
    ]

    bar_width  = img_width *0.4
    bar_height = img_height*0.9
    x1         = img_width/2 - bar_width/2
    x2         = img_width/2 + bar_width/2

    start_y = img_height/2 - bar_height/2
    for i, macro in enumerate(macros):
        color = legend[i][1]
        h = macro / (food.fat + food.carbs + food.protein) * bar_height
        # Macro bar
        draw.rectangle([x1, start_y, x2, start_y + h], fill=color)
        # Don't show legend and weight if they don't fit
        if h >= 32:
            # Macro text
            pad = 16
            txt = legend[i][0]
            tw, th = draw.textsize(txt, font=sans48bold)
            draw.text((x1 - tw - pad, start_y + h/2 - th/2), txt, fill=color, font=sans48bold, align="right")
            # Macro weight
            txt = str(round(macro,1))+"g"
            tw, th = draw.textsize(txt, font=sans48bold)
            tx = x1 + bar_width/2 - tw/2
            ty = start_y + h/2 - th/2
            draw.text((tx, ty), txt, fill="white", font=sans48bold, align="center")
        start_y += h

    return img

def make_calorie_breakdown(food : Food):
    size = 2048
    img = Image.new("RGB", (size, size), "white")
    draw = ImageDraw.Draw(img)

    fat_kcals     = food.fat*9
    carb_kcals    = food.net_carbs*4 + food.fiber*2
    protein_kcals = food.protein*4
    kcals         = fat_kcals + carb_kcals + protein_kcals
    part_fats     = fat_kcals     / kcals
    part_carbs    = carb_kcals    / kcals
    part_protein  = protein_kcals / kcals

    fat_color     = "#12a6a5"
    carb_color    = "#2b754c"
    protein_color = "#d63c3c"

    r = size*0.4
    margin = 3

    def draw_pieslice(start : float, end : float, color):
        end = max(end-margin, 0)
        draw.pieslice([size/2-r, size/2-r, size/2+r, size/2+r], start, end, fill=color)

    # Fats pieslice
    start  = 0
    end    = 360*part_fats
    draw_pieslice(start, end, fat_color)
    # Carbs pieslice
    start = end
    end   = start+360*part_carbs
    draw_pieslice(start, end, carb_color)
    # Protein pieslice
    start = end
    end   = start+360*part_protein
    draw_pieslice(start, end, protein_color)

    # White fill
    draw_centered_circle(draw, r*0.7, size/2, size/2, "white", True)
    # Kcals text
    draw_centered_text(draw, str(round(kcals))+" kcals", size/2, size*0.4, sans192bold, (0,0,0))
    # Fat % and grams text
    txt = "%d%% fat (%dg)" % (round(part_fats*100), round(food.fat))
    draw_centered_text(draw, txt, size/2, size*0.5, sans96bold, fat_color)
    # Carbs % and grams text
    txt = "%d%% carb (%dg)" % (round(part_carbs*100), round(food.carbs))
    draw_centered_text(draw, txt, size/2, size*0.55, sans96bold, carb_color)
    # Protein % and grams text
    txt = "%d%% protein (%dg)" % (round(part_protein*100), round(food.protein))
    draw_centered_text(draw, txt, size/2, size*0.6, sans96bold, protein_color)

    return img

def make_wheel(food : Food, wheel : (str, float), color):
    micros = [x[0] for x in wheel]
    drvs   = [x[1] for x in wheel]

    size = 2048
    img = Image.new("RGB", (size, size), "white")
    draw = ImageDraw.Draw(img)

    # Outer circle (100% of DRV)
    outer_r = size*0.35
    draw_centered_circle(draw, outer_r, size/2, size/2, color, True)
    # Inner circle (50% of DRV)
    draw_centered_circle(draw, outer_r/2, size/2, size/2, "white", False, width=5)

    for i in range(len(wheel)):
        micro = micros[i]
        drv   = drvs[i]
        rad   = i * 2 * math.pi / len(wheel)
        x = outer_r * math.cos(rad)
        y = outer_r * math.sin(rad)
        per_x = x + size/2
        per_y = y + size/2
        # Line from center point to outer circle perimeter
        draw.line((size/2, size/2, per_x, per_y), "white", width=5)
        # Text showing vitamin name and DRV%
        txt_x = x*1.2 + size/2
        txt_y = y*1.2 + size/2
        drv_pct = "N/A" if drv < 0 else str(round(100*drv)) + "%"
        text = micro + "\n (" + drv_pct + ")"
        draw_centered_text(draw, text, txt_x, txt_y, sans96bold, "black")
        if drv >= 0:
            # Line from center point to DRV value
            drv_x = x * min(drv, 1) + size/2
            drv_y = y * min(drv, 1) + size/2
            draw.line((size/2, size/2, drv_x, drv_y), "white", width=40)
    
    return img

def make_vitamin_wheel(food : Food):
    wheel = [
        ("A",       food.vit_a   / drv_a),
        ("B1",      food.vit_b1  / drv_b1),
        ("B2",      food.vit_b2  / drv_b2),
        ("B3",      food.vit_b3  / drv_b3),
        ("B5",      food.vit_b5  / drv_b5),
        ("B6",      food.vit_b6  / drv_b6),
        # ("B7",      food.vit_b7  / drv_b7),
        ("B9",      food.vit_b9  / drv_b9),
        ("B12",     food.vit_b12 / drv_b12),
        ("C",       food.vit_c   / drv_c),
        ("D",       food.vit_d   / drv_d),
        ("E",       food.vit_e   / drv_e),
        ("K",       food.vit_k   / drv_k),
        ("Choline", food.choline / drv_choline),
    ]
    return make_wheel(food, wheel, "#9b4f96")

def make_mineral_wheel(food : Food):
    wheel = [
        ("Potassium",  food.potassium  / drv_potassium),
        ("Sodium",     food.sodium     / drv_sodium),
        ("Calcium",    food.calcium    / drv_calcium),
        ("Phosphorus", food.phosphorus / drv_phosphorus),
        ("Magnesium",  food.magnesium  / drv_magnesium),
        ("Iron",       food.iron       / drv_iron),
        ("Zinc",       food.zinc       / drv_zinc),
        ("Manganese",  food.manganese  / drv_manganese),
        ("Copper",     food.copper     / drv_copper),
        # ("Molybdenum", food.molybdenum / drv_molybdenum),
        ("Selenium",   food.selenium   / drv_selenium),
        # ("Chloride",   food.chloride   / drv_chloride),
    ]
    return make_wheel(food, wheel, "#12a6a5")

def make_misc_stats(food : Food):
    img = Image.new("RGB", (1, 1), "white") # Size doesn't matter because we're gonna resize anyway
    draw = ImageDraw.Draw(img)

    trans_fats_text = "N/A"
    if food.trans_fats >= 0:
        trans_fats_text = str(round(food.trans_fats,1)) + "g"

    cell_contents = [
        ("Omega-3", "%d%% (%dmg)" % (round(food.omega_3/drv_omega_3*100), round(food.omega_3))),
        ("Omega-6", "%d%% (%dmg)" % (round(food.omega_6/drv_omega_6*100), round(food.omega_6))),
        ("Water", str(round(food.water)) + "ml"),
        ("Trans fats", trans_fats_text),
        ("Net carbs", str(round(food.net_carbs,1)) + "g"),
    ]

    # Resize image according to this potentially long row
    cell_w, cell_h = draw.textsize("100% (1000mg)", font=sans96bold)
    cell_w *= 1.1 # Margin
    cell_h *= 1.1 # Margin
    cell_margin    = 32
    table_w        = cell_w*2 + cell_margin
    table_h        = cell_h*5 + cell_margin*4
    img  = img.resize((round(table_w), round(table_h)))
    draw = ImageDraw.Draw(img)

    for i in range(5):
        # Left cell
        x1 = 0
        x2 = cell_w
        y1 = i*cell_h + i*cell_margin
        y2 = y1 + cell_h
        draw.rectangle([x1, y1, x2, y2], fill="#12a6a5")
        draw.text((x1+32, y1), cell_contents[i][0], fill="white", font=sans96bold, align="left")
        # Right cell
        x1 = x2 + cell_margin
        x2 = table_w
        draw.rectangle([x1, y1, x2, y2], fill="#12a6a5")
        draw.text((x1+32, y1), cell_contents[i][1], fill="white", font=sans96bold, align="left")

    return img

def make_nutritional_profile(food : Food, dir_name : str):
    macros_img   = make_macros_bar(food)
    kcals_img    = make_calorie_breakdown(food)
    vitamins_img = make_vitamin_wheel(food)
    minerals_img = make_mineral_wheel(food)
    stats_img    = make_misc_stats(food)

    # macros_img  .save(food.name+"_macros.bmp")
    # kcals_img   .save(food.name+"_calories.bmp")
    # vitamins_img.save(food.name+"_vitamins.bmp")
    # minerals_img.save(food.name+"_minerals.bmp")
    # stats_img   .save(food.name+"_stats.bmp")

    size = (2816, 2048)
    img = Image.new("RGB", size, "white")
    draw = ImageDraw.Draw(img)
    # Macros bar
    img.paste(macros_img, (0, 0))
    # Mineral wheel
    minerals_img = minerals_img.resize((round(minerals_img.width/2), round(minerals_img.height/2)), resample=Image.LANCZOS)
    bar_w = 768
    img.paste(minerals_img, (bar_w, size[1] - minerals_img.height))
    # Vitamin wheel
    vitamins_img = vitamins_img.resize((round(vitamins_img.width/2), round(vitamins_img.height/2)), resample=Image.LANCZOS)
    img.paste(vitamins_img, (bar_w + minerals_img.width, size[1] - vitamins_img.height))
    # Calorie breakdown
    kcals_img = kcals_img.resize((round(kcals_img.width/2), round(kcals_img.height/2)), resample=Image.LANCZOS)
    img.paste(kcals_img, (bar_w + minerals_img.width, size[1] - kcals_img.height - vitamins_img.height))
    # Misc stats
    stats_img = stats_img.resize((round(stats_img.width/2), round(stats_img.height/2)), resample=Image.LANCZOS)
    x = round(bar_w + minerals_img.width/2 - stats_img.width/2)
    img.paste(stats_img, (x, size[1] - minerals_img.height - stats_img.height))
    # Serving description
    x = bar_w + minerals_img.width/2
    draw_centered_text(draw, "Nutritional contents of", x, size[1]*0.07, sans96bold, "black")
    wrapped = "\n".join(textwrap.wrap(food.serving_desc, width=15))
    draw_centered_text(draw, wrapped, x, size[1]*0.2, sans128bold, "black")
    # Bottom-right FDC ID
    txt = "FDC ID "+str(food.fdc_id)
    tw, th = draw.textsize(txt, font=sans48bold)
    draw.text((size[0]-tw-1, size[1]-th-1), txt, fill="grey", font=sans48bold)

    img = img.resize((round(img.width/4), round(img.height/4)), resample=Image.LANCZOS)
    fname = food.name.replace(" ", "_") + "_nutrition.jpg"
    img.save(dir_name+"/"+fname, quality=95)

fname      = "dairy"
dir_name   = fname+"_profiles"
foods_data = read_foods(fname)
data_file  = open("nut_sheet.csv", "r")
entries    = data_file.readlines()
os.mkdir(dir_name) # Images will be saved here

for food_data in foods_data:
    food = get_nutrients(food_data)
    if food == None:
        continue
    make_nutritional_profile(food, dir_name)

    # Debug prints
    # attrs = vars(food)
    # print("--------------------")
    # print(food.name+"\n"+"\n".join("%s=%s" % item for item in attrs.items()))

data_file.close()
