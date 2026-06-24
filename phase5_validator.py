import os
import pandas as pd
from common.config import PHASE4_OUTPUT_DIR, PHASE5_OUTPUT_DIR
from common.logger import get_logger
from common.checkpoint import is_completed, mark_completed
from common.metrics import set_metric, save_metrics

logger = get_logger("phase5")
os.makedirs(PHASE5_OUTPUT_DIR, exist_ok=True)

# ============================================================
# ISSUE 1 — FOOD & BEVERAGE: PRODUCT-KEYWORD BASED SPLIT
# Phase 4 renamed subcategories so we use product names instead
# ============================================================
FOOD_PRODUCT_KEYWORDS = [
    # Beverages
    'tea', 'coffee', 'juice', 'drink', 'beverage', 'water bottle',
    'smoothie', 'shake', 'lassi', 'buttermilk', 'coconut water',
    'energy drink', 'soft drink', 'soda',
    # Dairy
    'milk', 'paneer', 'ghee', 'butter', 'cheese', 'curd', 'yogurt',
    'cream', 'dairy', 'whey',
    # Bakery & Confectionery
    'bread', 'cake', 'biscuit', 'cookie', 'chocolate', 'candy',
    'sweet', 'mithai', 'laddoo', 'barfi', 'halwa', 'gulab jamun',
    'rasgulla', 'confectionery', 'pastry', 'muffin', 'cupcake',
    'bakery', 'toffee',
    # Snacks
    'snack', 'namkeen', 'bhujia', 'chiwda', 'popcorn', 'chips',
    'peanut snack', 'farsan', 'gathiya', 'makhana',
    # Condiments & Sauces
    'pickle', 'sauce', 'ketchup', 'chutney', 'paste', 'jam',
    'mayonnaise', 'vinegar', 'mustard', 'dressing', 'achar',
    # Oils
    'edible oil', 'cooking oil', 'sunflower oil', 'mustard oil',
    'coconut oil', 'groundnut oil', 'olive oil', 'sesame oil',
    'rice bran oil', 'soybean oil', 'palm oil', 'canola oil',
    # Spices & Herbs (food grade)
    'turmeric', 'black pepper', 'cumin', 'coriander', 'cardamom',
    'cinnamon', 'clove', 'ginger powder', 'chilli powder',
    'masala', 'spice blend', 'herb blend',
    # Grains, Cereals, Pulses
    'basmati rice', 'white rice', 'brown rice', 'rice variety',
    'wheat flour', 'atta', 'maida', 'besan', 'flour variety',
    'dal variety', 'lentil variety', 'pulse variety', 'chana',
    'rajma', 'moong', 'toor dal', 'urad dal', 'barley grain',
    'oats', 'quinoa', 'millet', 'sorghum', 'corn flour',
    # Fresh Produce
    'fresh tomato', 'fresh mango', 'fresh onion', 'fresh garlic',
    'fresh ginger', 'fresh vegetable', 'fresh fruit', 'fresh potato',
    # Frozen & Processed
    'frozen food', 'frozen meal', 'frozen vegetable', 'frozen fruit',
    'frozen chicken', 'frozen fish', 'instant food', 'ready to eat',
    'ready-to-eat', 'rte food', 'canned food', 'preserved food',
    # Meat & Seafood
    'chicken cut', 'fresh chicken', 'mutton', 'lamb cut', 'beef',
    'fresh fish', 'prawn', 'shrimp', 'seafood', 'tuna', 'salmon',
    # Tobacco
    'cigarette', 'cigar', 'tobacco product',
    # Baby Food
    'baby food', 'infant formula', 'baby cereal', 'baby puree',
    # Health Food
    'protein powder', 'whey protein', 'mass gainer', 'pre-workout supplement',
    'post-workout', 'bcaa supplement', 'creatine supplement',
    'sports drink', 'electrolyte drink for athlete',
]

# Subcategory mapping for food products based on product keywords
FOOD_SUBCATEGORY_MAP = [
    (['tea', 'coffee', 'juice', 'beverage', 'drink', 'lassi', 'buttermilk',
      'coconut water', 'energy drink', 'smoothie', 'shake'], 'Beverages (Tea, Coffee, Juices)'),
    (['milk', 'paneer', 'ghee', 'butter', 'cheese', 'curd', 'yogurt',
      'cream', 'dairy', 'whey protein'], 'Dairy Products & Alternatives'),
    (['bread', 'cake', 'biscuit', 'cookie', 'chocolate', 'candy', 'sweet',
      'mithai', 'laddoo', 'barfi', 'halwa', 'gulab jamun', 'rasgulla',
      'confectionery', 'pastry', 'muffin', 'cupcake', 'bakery', 'toffee'], 'Bakery & Confectionery Products'),
    (['snack', 'namkeen', 'bhujia', 'chiwda', 'popcorn', 'chips',
      'farsan', 'gathiya', 'makhana', 'peanut snack'], 'Snacks & Namkeens'),
    (['pickle', 'ketchup', 'chutney', 'jam', 'sauce', 'paste',
      'mayonnaise', 'vinegar', 'mustard', 'dressing', 'achar'], 'Condiments & Sauces'),
    (['edible oil', 'cooking oil', 'sunflower oil', 'mustard oil',
      'coconut oil', 'groundnut oil', 'olive oil', 'sesame oil',
      'rice bran oil', 'soybean oil', 'palm oil', 'canola oil'], 'Edible Oils & Fats'),
    (['frozen food', 'frozen meal', 'frozen vegetable', 'frozen fruit',
      'frozen chicken', 'frozen fish', 'frozen prawn'], 'Frozen & Processed Foods'),
    (['instant food', 'ready to eat', 'ready-to-eat', 'rte food',
      'canned food', 'preserved food'], 'Ready-to-Eat & Instant Foods'),
    (['chicken cut', 'fresh chicken', 'mutton', 'lamb cut', 'fresh fish',
      'prawn', 'shrimp', 'seafood', 'tuna', 'salmon'], 'Meat, Poultry & Seafood'),
    (['cigarette', 'cigar', 'tobacco product'], 'Tobacco & Smoking Products'),
    (['baby food', 'infant formula', 'baby cereal', 'baby puree'], 'Baby Food Products'),
    (['protein powder', 'whey protein', 'mass gainer', 'pre-workout supplement',
      'bcaa supplement', 'creatine supplement', 'sports drink',
      'electrolyte drink for athlete'], 'Sports Nutrition Products'),
]

def get_food_subcategory(product_name: str) -> str:
    lower = product_name.lower()
    for keywords, subcategory in FOOD_SUBCATEGORY_MAP:
        if any(kw in lower for kw in keywords):
            return subcategory
    return 'Food & Beverage Products'

def is_food_product(product_name: str) -> bool:
    lower = product_name.lower()
    return any(kw in lower for kw in FOOD_PRODUCT_KEYWORDS)

# ============================================================
# ISSUE 2 — INDUSTRIAL TOOLS SPLIT
# ============================================================
INDUSTRIAL_TOOLS_SPLIT = {
    # Packaging Machinery
    'shrink wrap': 'Packaging Machinery',
    'packing machine': 'Packaging Machinery',
    'filling machine': 'Packaging Machinery',
    'sealing machine': 'Packaging Machinery',
    'labeling machine': 'Packaging Machinery',
    'cartoning': 'Packaging Machinery',
    'sachet': 'Packaging Machinery',
    'pouch': 'Packaging Machinery',
    'form fill seal': 'Packaging Machinery',
    'wrapping machine': 'Packaging Machinery',
    'packaging line': 'Packaging Machinery',
    'bag in box': 'Packaging Machinery',
    'case packer': 'Packaging Machinery',
    'carton erector': 'Packaging Machinery',
    'carton sealer': 'Packaging Machinery',
    'coding machine': 'Packaging Machinery',
    'flow wrap': 'Packaging Machinery',
    'sleeve wrap': 'Packaging Machinery',
    'skin pack': 'Packaging Machinery',
    'auger fill': 'Packaging Machinery',
    'volumetric': 'Packaging Machinery',
    'granule fill': 'Packaging Machinery',
    'powder sachet': 'Packaging Machinery',
    'stick pack': 'Packaging Machinery',
    'vacuum brick': 'Packaging Machinery',
    'jar & can packaging': 'Packaging Machinery',
    'packaging forming': 'Packaging Machinery',
    'eco-friendly packaging machine': 'Packaging Machinery',
    'multi-lane pack': 'Packaging Machinery',
    'induction seal': 'Packaging Machinery',
    'gluing machine': 'Packaging Machinery',
    'bottle labeler': 'Packaging Machinery',
    'box taping': 'Packaging Machinery',
    'heat sealing': 'Packaging Machinery',
    'cling film wrapping': 'Packaging Machinery',
    'clamshell sealing': 'Packaging Machinery',
    'foil wrapping machine': 'Packaging Machinery',
    'multi-function packaging': 'Packaging Machinery',
    'beverage multipack': 'Packaging Machinery',
    'batch coding': 'Packaging Machinery',
    'thermal transfer overprint': 'Packaging Machinery',
    'zipper pouch sealer': 'Packaging Machinery',
    'weighmetric filling': 'Packaging Machinery',
    'vertical form fill': 'Packaging Machinery',
    'horizontal form fill': 'Packaging Machinery',
    'stand-up pouch packing': 'Packaging Machinery',
    'pet bottle shrink': 'Packaging Machinery',

    # Metal & Scrap Materials
    'scrap': 'Metal & Scrap Materials',
    'metal coil': 'Metal & Scrap Materials',
    'metal rod': 'Metal & Scrap Materials',
    'steel pipe': 'Metal & Scrap Materials',
    'aluminum extrusion': 'Metal & Scrap Materials',
    'copper sheet': 'Metal & Scrap Materials',
    'brass scrap': 'Metal & Scrap Materials',
    'aluminum pipe': 'Metal & Scrap Materials',
    'stainless steel sheet': 'Metal & Scrap Materials',
    'metal foil': 'Metal & Scrap Materials',
    'metal plate': 'Metal & Scrap Materials',
    'metal forging': 'Metal & Scrap Materials',
    'heat resistant alloy': 'Metal & Scrap Materials',
    'recycled alloy': 'Metal & Scrap Materials',
    'metal supply': 'Metal & Scrap Materials',
    'aluminum truss': 'Metal & Scrap Materials',
    'steel truss': 'Metal & Scrap Materials',
    'expanded metal': 'Metal & Scrap Materials',
    'cold rolled steel': 'Metal & Scrap Materials',
    'metal conductor': 'Metal & Scrap Materials',
    'metal baling': 'Metal & Scrap Materials',
    'steel turnings': 'Metal & Scrap Materials',
    'nickel alloy': 'Metal & Scrap Materials',
    'titanium sheet': 'Metal & Scrap Materials',
    'titanium rod': 'Metal & Scrap Materials',
    'metal flanges': 'Metal & Scrap Materials',
    'metal gratings': 'Metal & Scrap Materials',
    'ferrous metal': 'Metal & Scrap Materials',
    'copper pipes': 'Metal & Scrap Materials',
    'aluminum scrap': 'Metal & Scrap Materials',
    'copper scrap': 'Metal & Scrap Materials',
    'industrial metal': 'Metal & Scrap Materials',
    'metal coils (all': 'Metal & Scrap Materials',
    'decorative metal panel': 'Metal & Scrap Materials',
    'precision metal': 'Metal & Scrap Materials',

    # Cold Chain & Refrigeration
    'cold room': 'Cold Chain & Refrigeration Equipment',
    'refriger': 'Cold Chain & Refrigeration Equipment',
    'cold pack': 'Cold Chain & Refrigeration Equipment',
    'cold storage': 'Cold Chain & Refrigeration Equipment',
    'frozen storage': 'Cold Chain & Refrigeration Equipment',
    'reefer container': 'Cold Chain & Refrigeration Equipment',
    'condensing unit': 'Cold Chain & Refrigeration Equipment',
    'insulated delivery': 'Cold Chain & Refrigeration Equipment',
    'cold box': 'Cold Chain & Refrigeration Equipment',
    'multi-commodity cold': 'Cold Chain & Refrigeration Equipment',
    'refrigerant': 'Cold Chain & Refrigeration Equipment',
    'controlled atmosphere': 'Cold Chain & Refrigeration Equipment',
    'portable cold box': 'Cold Chain & Refrigeration Equipment',
    'bike-mounted refriger': 'Cold Chain & Refrigeration Equipment',

    # Stage & Event Equipment
    'stage platform': 'Stage & Event Equipment',
    'stage flooring': 'Stage & Event Equipment',
    'stage railing': 'Stage & Event Equipment',
    'stage ramp': 'Stage & Event Equipment',
    'stage riser': 'Stage & Event Equipment',
    'stage roof': 'Stage & Event Equipment',
    'stage curtain': 'Stage & Event Equipment',
    'stage canopy': 'Stage & Event Equipment',
    'stage drape': 'Stage & Event Equipment',
    'dj booth': 'Stage & Event Equipment',
    'dj stage': 'Stage & Event Equipment',
    'truss circle': 'Stage & Event Equipment',
    'truss clamp': 'Stage & Event Equipment',
    'box truss': 'Stage & Event Equipment',
    'lighting truss stand': 'Stage & Event Equipment',
    'backdrop frame': 'Stage & Event Equipment',
    'scaffold tower for stage': 'Stage & Event Equipment',
    'mic stand': 'Stage & Event Equipment',
    'studio acoustic': 'Stage & Event Equipment',
    'studio furniture': 'Stage & Event Equipment',
    'vocal booth': 'Stage & Event Equipment',
    'pipe and drape': 'Stage & Event Equipment',
    'portable stage': 'Stage & Event Equipment',

    # Equipment Rental & Maintenance Services
    'rental': 'Equipment Rental & Maintenance Services',
    'leasing': 'Equipment Rental & Maintenance Services',
    ' maintenance': 'Equipment Rental & Maintenance Services',
    'repair service': 'Equipment Rental & Maintenance Services',
    ' amc': 'Equipment Rental & Maintenance Services',
    'servicing': 'Equipment Rental & Maintenance Services',
    'installation service': 'Equipment Rental & Maintenance Services',
    'commissioning': 'Equipment Rental & Maintenance Services',
    'breakdown service': 'Equipment Rental & Maintenance Services',
    'service contract': 'Equipment Rental & Maintenance Services',
    'on-site equipment': 'Equipment Rental & Maintenance Services',
    'preventive maintenance': 'Equipment Rental & Maintenance Services',
    'equipment insurance': 'Equipment Rental & Maintenance Services',
    'machinery servicing': 'Equipment Rental & Maintenance Services',
    'machinery repair': 'Equipment Rental & Maintenance Services',
    'operator & technician': 'Equipment Rental & Maintenance Services',
    'buyback & exchange': 'Equipment Rental & Maintenance Services',
    'asset tracking': 'Equipment Rental & Maintenance Services',

    # Garment & Apparel Production Tools
    'garment sample': 'Apparel & Fashion',
    'apparel cad': 'Apparel & Fashion',
    'fit sample': 'Apparel & Fashion',
    'lingerie prototype': 'Apparel & Fashion',
    'luxury fashion sample': 'Apparel & Fashion',
    'print sample unit': 'Apparel & Fashion',
    'trim & notion sampling': 'Apparel & Fashion',
    'size set sample': 'Apparel & Fashion',
    'pattern testing': 'Apparel & Fashion',
    'yarn & thread sampling': 'Apparel & Fashion',
    'colorway sample': 'Apparel & Fashion',
    'embroidery sample': 'Apparel & Fashion',
    'fabric swatch': 'Apparel & Fashion',
    'pre-production sample': 'Apparel & Fashion',
    'sustainable apparel sampling': 'Apparel & Fashion',
    'custom apparel prototyping': 'Apparel & Fashion',

    # Agricultural equipment
    'farm equipment leasing': 'Agricultural Machinery',
    'farm mechanization': 'Agricultural Machinery',
    'farm trailer': 'Agricultural Machinery',
    'fertilizer mixer': 'Agricultural Machinery',
    'fertilizer spreader': 'Agricultural Machinery',
    'seed dibbler': 'Agricultural Machinery',
    'seed grader': 'Agricultural Machinery',
    'direct seeder': 'Agricultural Machinery',
    'transplanter': 'Agricultural Machinery',
    'soil auger': 'Agricultural Machinery',
    'nursery seedling machine': 'Agricultural Machinery',
    'vermicompositing unit': 'Agricultural Machinery',
    'trellis support': 'Agricultural Machinery',
    'ground cover film': 'Agricultural Machinery',
    'planter pot for greenhouse': 'Agricultural Machinery',
    'polyhouse construction': 'Agricultural Machinery',
    'venturi injector': 'Agricultural Machinery',
    'brush cutter': 'Agricultural Machinery',
    'irrigation pump': 'Irrigation Systems & Equipment',
    'irrigation system': 'Irrigation Systems & Equipment',
    'tractor trailer': 'Agricultural Machinery',
    'agricultural crate': 'Agricultural Machinery',
    'agricultural equipment bearing': 'Agricultural Machinery',
    'agricultural equipment maintenance': 'Equipment Rental & Maintenance Services',
    'exporters of agri': None,  # business entity — remove
    'farm tool &': None,  # truncated — remove
}

# ============================================================
# ISSUE 3 — Healthcare IT Solutions in wrong categories
# ============================================================
HEALTHCARE_IT_WRONG_CATS = {
    'Health & Personal Care',
    'Electrical & Electronics',
    'Machinery & Equipment',
}

# ============================================================
# ISSUE 4 — Other specific fixes
# ============================================================
SPECIFIC_FIXES = {
    # Retail POS Software in Apparel — move to Software & IT Solutions
    ('Apparel & Fashion', 'Retail Point of Sale (POS) Software'): (
        'Software & IT Solutions', 'CRM & Sales Automation Software'),

    # PCB & Electronic Components in Chemicals — move to Electrical
    ('Chemicals & Raw Materials', 'PCB & Electronic Components'): (
        'Electrical & Electronics', 'PCB & Electronic Components'),

    # Excess Inventory in Chemicals — delete
    ('Chemicals & Raw Materials', 'Excess Inventory'): None,

    # Excess Inventory in Machinery — delete
    ('Machinery & Equipment', 'Excess Inventory'): None,

    # Certification Services in Chemicals — move to Services
    ('Chemicals & Raw Materials', 'Certification Services'): (
        'Services & Support', 'Certification & Compliance Services'),

    # Engineering & Technical Services in Home & Lifestyle — move to Services
    ('Home & Lifestyle', 'Engineering & Technical Services'): (
        'Services & Support', 'Engineering & Technical Services'),

    # Engineering & Technical Services in Machinery — move to Services
    ('Machinery & Equipment', 'Engineering & Technical Services'): (
        'Services & Support', 'Engineering & Technical Services'),

    # PCB in Machinery — move to Electrical
    ('Machinery & Equipment', 'PCB & Electronic Components'): (
        'Electrical & Electronics', 'PCB & Electronic Components'),

    # Medical Waste in Machinery — move to Health
    ('Machinery & Equipment', 'Medical Waste Disposal Products'): (
        'Health & Personal Care', 'Medical Consumables'),

    # Healthcare IT Solutions in Health — move to Software
    ('Health & Personal Care', 'Healthcare IT Solutions'): (
        'Software & IT Solutions', 'Healthcare IT Software'),

    # Healthcare IT Solutions in Electrical — move to Software
    ('Electrical & Electronics', 'Healthcare IT Solutions'): (
        'Software & IT Solutions', 'Healthcare IT Software'),

    # Healthcare IT Solutions in Machinery — move to Software
    ('Machinery & Equipment', 'Healthcare IT Solutions'): (
        'Software & IT Solutions', 'Healthcare IT Software'),

    # Fleet Management Solutions in Automotive — merge into Fleet Management Services
    ('Automotive & Transport', 'Fleet Management Solutions'): (
        'Automotive & Transport', 'Fleet Management Services'),

    # Retreaded Tyres in Automotive — merge into Tyre Retreading & Recycling
    ('Automotive & Transport', 'Retreated Tyres'): (
        'Automotive & Transport', 'Tyre Retreading & Recycling'),

    # Biofertilizers in Chemicals — move to Agriculture
    ('Chemicals & Raw Materials', 'Biofertilizers'): (
        'Machinery & Equipment', 'Agricultural Machinery'),

    # Organic Fertilizers in Chemicals — move to Agriculture Machinery
    ('Chemicals & Raw Materials', 'Organic Fertilizers'): (
        'Machinery & Equipment', 'Agricultural Machinery'),

    # Excess Inventory Management in Services — delete
    ('Services & Support', 'Excess Inventory Management'): None,

    # Construction Safety Equipment in Machinery — move to Construction
    ('Machinery & Equipment', 'Construction Safety Equipment'): (
        'Construction & Infrastructure', 'Construction Safety Equipment'),

    # Metal Ingots in Machinery — move to Chemicals
    ('Machinery & Equipment', 'Metal Ingots, Sheets, Rods & Wires'): (
        'Chemicals & Raw Materials', 'Metal Ingots, Sheets, Rods & Wires'),

    # Power Tools in Machinery — move to Tools & Hardware
    ('Machinery & Equipment', 'Power Tools'): (
        'Tools & Hardware', 'Power Tools (Drills, Grinders, Saws)'),

    ('Machinery & Equipment', 'Power Tools (Drills, Grinders, Saws)'): (
        'Tools & Hardware', 'Power Tools (Drills, Grinders, Saws)'),

    ('Machinery & Equipment', 'Hand Tools'): (
        'Tools & Hardware', 'Hand Tools (Wrenches, Hammers, Screwdrivers)'),

    # Welding Tools in Machinery — move to Tools & Hardware
    ('Machinery & Equipment', 'Welding Tools & Accessories'): (
        'Tools & Hardware', 'Welding Tools & Accessories'),

    # Hydraulic Tools in Machinery — move to Tools & Hardware
    ('Machinery & Equipment', 'Hydraulic Tools'): (
        'Tools & Hardware', 'Hydraulic Tools'),

    # Cutting Tools in Machinery — check if industrial or hardware
    # Keep in Machinery as Cutting Machines (industrial grade)

    # Smart Home Devices in Home — keep
    # Engineering in Electrical — move to Services
    ('Electrical & Electronics', 'Engineering & Technical Services'): (
        'Services & Support', 'Engineering & Technical Services'),

    # Cleaning tools in Office — keep (office cleaning supplies is valid)
}

# Products to delete entirely (truncated, business entities, non-products)
PRODUCTS_TO_DELETE = {
    'Farm Tool &',          # truncated
    'Wood &',               # truncated
    'Exporters of Agri Equipment',  # business entity
    'ODM Tool',             # vague
    'Oem Earthmoving Machinery Spares',  # business entity
    'Equipment',            # single word generic
    'Farm Equipment',       # too generic
}

# SOFTWARE DETECTION
NON_SOFTWARE_CATEGORIES = {
    'Apparel & Fashion', 'Agriculture & Food Products', 'Agriculture & Farming',
    'Food & Beverage', 'Machinery & Equipment', 'Chemicals & Raw Materials',
    'Electrical & Electronics', 'Construction & Infrastructure',
    'Health & Personal Care', 'Automotive & Transport', 'Home & Lifestyle',
    'Tools & Hardware', 'Packaging & Printing', 'Office Supplies & Equipment',
    'Sports & Entertainment',
}
SOFTWARE_KEYWORDS = ['software', 'erp', 'crm', 'saas', 'management system',
                     'tracking system', 'automation system', 'information system',
                     'management platform', 'analytics platform']
PHYSICAL_WHITELIST = ['platform bed', 'platform scale', 'platform ladder',
                      'platform lift', 'platform shoe', 'scissor lift',
                      'dashboard cover', 'dashboard organizer', 'smart bulb',
                      'alarm system', 'grout filling', 'home lift',
                      'automation system installation', 'fleet tracking']

def is_software(name: str) -> bool:
    lower = name.lower().strip()
    if any(p in lower for p in PHYSICAL_WHITELIST):
        return False
    padded = f' {lower} '
    return any(f' {kw} ' in padded or padded.strip().endswith(kw)
               for kw in SOFTWARE_KEYWORDS)

def get_industrial_tools_subcategory(product_name: str) -> str:
    lower = ' ' + product_name.lower() + ' '
    for keyword, subcategory in INDUSTRIAL_TOOLS_SPLIT.items():
        if keyword in lower:
            return subcategory
    return 'Industrial Tools'

def run():
    if is_completed('phase5'):
        return

    logger.info('Starting Phase 5 — Validator v6 (All 9 Issues)')

    input_path = os.path.join(PHASE4_OUTPUT_DIR, 'normalized.csv')
    if not os.path.exists(input_path):
        raise FileNotFoundError(f'Phase 4 output not found: {input_path}')

    df = pd.read_csv(input_path)
    if 'attributes' in df.columns:
        df = df.drop(columns=['attributes'])

    initial = len(df)
    logger.info(f'Input rows: {initial}')
    rows_to_delete = []

    # ── ISSUE 9 — DELETE TRUNCATED & BUSINESS ENTITY PRODUCTS ────
    delete_mask = df['product_category'].isin(PRODUCTS_TO_DELETE)
    rows_to_delete.extend(df[delete_mask].index.tolist())
    logger.info(f'Issue 9: Marked {delete_mask.sum()} truncated/invalid products for deletion')

    # ── ISSUE 1 — FOOD & BEVERAGE KEYWORD-BASED SPLIT ────────────
    # Find food products scattered across all categories
    food_found = 0
    for idx, row in df.iterrows():
        if idx in rows_to_delete:
            continue
        prod = str(row['product_category'])
        if is_food_product(prod):
            # Only move if currently in wrong category
            if row['category'] not in ('Food & Beverage', 'Agriculture & Farming',
                                        'Health & Personal Care', 'Packaging & Printing',
                                        'Machinery & Equipment', 'Services & Support'):
                sub = get_food_subcategory(prod)
                df.at[idx, 'category'] = 'Food & Beverage'
                df.at[idx, 'subcategory'] = sub
                food_found += 1
    logger.info(f'Issue 1: Moved {food_found} food products to Food & Beverage')

    # ── ISSUE 2 — INDUSTRIAL TOOLS SPLIT ─────────────────────────
    it_mask = (
        (df['category'] == 'Machinery & Equipment') &
        (df['subcategory'] == 'Industrial Tools')
    )
    it_reclassified = 0
    for idx, row in df[it_mask].iterrows():
        if idx in rows_to_delete:
            continue
        prod = str(row['product_category'])
        new_sub = get_industrial_tools_subcategory(prod)
        if new_sub == 'Apparel & Fashion':
            df.at[idx, 'category'] = 'Apparel & Fashion'
            df.at[idx, 'subcategory'] = 'Garment Accessories & Trims'
            it_reclassified += 1
        elif new_sub == 'Agricultural Machinery':
            df.at[idx, 'subcategory'] = 'Agricultural Machinery'
            it_reclassified += 1
        elif new_sub == 'Irrigation Systems & Equipment':
            df.at[idx, 'subcategory'] = 'Irrigation Systems & Equipment'
            it_reclassified += 1
        elif new_sub is None:
            rows_to_delete.append(idx)
        elif new_sub != 'Industrial Tools':
            df.at[idx, 'subcategory'] = new_sub
            it_reclassified += 1

    logger.info(f'Issue 2: Industrial Tools split — {it_reclassified} products reclassified')

    # ── ISSUES 3-8 — SPECIFIC CATEGORY/SUBCATEGORY FIXES ─────────
    specific_fixed = 0
    specific_deleted = 0
    for idx, row in df.iterrows():
        if idx in rows_to_delete:
            continue
        key = (str(row['category']), str(row['subcategory']))
        if key in SPECIFIC_FIXES:
            dest = SPECIFIC_FIXES[key]
            if dest is None:
                rows_to_delete.append(idx)
                specific_deleted += 1
            else:
                df.at[idx, 'category'] = dest[0]
                df.at[idx, 'subcategory'] = dest[1]
                specific_fixed += 1

    logger.info(f'Issues 3-8: {specific_fixed} products fixed, {specific_deleted} deleted')

    # ── APPLY DELETIONS ───────────────────────────────────────────
    df = df.drop(index=list(set(rows_to_delete)))
    logger.info(f'Total rows deleted: {len(set(rows_to_delete))}')

    # ── SOFTWARE MISPLACEMENT ────────────────────────────────────
    misplaced_mask = df.apply(
        lambda row: row['category'] in NON_SOFTWARE_CATEGORIES
                    and is_software(str(row['product_category'])),
        axis=1
    )
    if misplaced_mask.sum():
        logger.warning(f'Misplaced software auto-corrected: {misplaced_mask.sum()}')
        df.loc[misplaced_mask, 'category'] = 'Software & IT Solutions'
        df.loc[misplaced_mask, 'subcategory'] = 'Industry-Specific Software'

    # ── DEDUPLICATION ────────────────────────────────────────────
    before = len(df)
    df = df.drop_duplicates()
    logger.info(f'Exact duplicates removed: {before - len(df)}')

    before = len(df)
    df['sub_len'] = df['subcategory'].str.len()
    df = df.sort_values('sub_len', ascending=False)
    df = df.drop_duplicates(subset=['category', 'product_category'], keep='first')
    df = df.drop(columns=['sub_len'])
    logger.info(f'Cross-subcategory duplicates resolved: {before - len(df)}')

    before = len(df)
    df['_lower'] = df['product_category'].str.lower().str.strip()
    df = df.drop_duplicates(subset=['_lower'], keep='first')
    df = df.drop(columns=['_lower'])
    logger.info(f'Case duplicates resolved: {before - len(df)}')

    # ── DROP EMPTY ───────────────────────────────────────────────
    df = df.dropna(subset=['category', 'subcategory', 'product_category'])
    df = df[df['product_category'].str.strip() != '']

    # ── SORT ─────────────────────────────────────────────────────
    df = df.sort_values(['category', 'subcategory', 'product_category']).reset_index(drop=True)

    final = len(df)
    cat_count = df['category'].nunique()
    sub_count = df['subcategory'].nunique()

    # ── VALIDATION REPORT ────────────────────────────────────────
    food_bev = len(df[df['category'] == 'Food & Beverage'])
    agri = len(df[df['category'] == 'Agriculture & Farming'])
    it_remaining = len(df[(df['category'] == 'Machinery & Equipment') &
                          (df['subcategory'] == 'Industrial Tools')])
    hc_it_wrong = len(df[df['subcategory'] == 'Healthcare IT Solutions'])
    sw_subs = df[df['category'] == 'Software & IT Solutions']['subcategory'].value_counts()
    excess = len(df[df['subcategory'] == 'Excess Inventory'])

    logger.info(f'\n{"="*55}')
    logger.info('VALIDATION RESULTS:')
    logger.info(f'  Issue 1 — Food & Beverage: {food_bev} products (target: 200+)')
    logger.info(f'  Issue 2 — Industrial Tools remaining: {it_remaining} (was 461)')
    logger.info(f'  Issue 3 — Healthcare IT Solutions wrong cats: {hc_it_wrong} (target: 0)')
    logger.info(f'  Issue 6 — Excess Inventory subcategory: {excess} (target: 0)')
    logger.info(f'{"="*55}')
    logger.info(f'\nSoftware subcategories:\n{sw_subs.to_string()}')
    logger.info(f'\nCategory distribution:\n{df["category"].value_counts().to_string()}')

    set_metric('final_products', final)
    set_metric('final_subcategories', sub_count)
    set_metric('final_categories', cat_count)
    set_metric('food_beverage_products', food_bev)
    set_metric('agriculture_farming_products', agri)
    set_metric('industrial_tools_remaining', it_remaining)

    output_path = os.path.join(PHASE5_OUTPUT_DIR, 'final_taxonomy.csv')
    df.to_csv(output_path, index=False, encoding='utf-8')
    logger.info(f'Output: {output_path} ({final} rows | {sub_count} subcategories | {cat_count} categories)')

    save_metrics()
    mark_completed('phase5')
    logger.info('Phase 5 complete.')

if __name__ == '__main__':
    run()
