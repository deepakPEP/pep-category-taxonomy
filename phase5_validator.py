import os
import pandas as pd
from common.config import PHASE4_OUTPUT_DIR, PHASE5_OUTPUT_DIR
from common.logger import get_logger
from common.checkpoint import is_completed, mark_completed
from common.metrics import set_metric, save_metrics

logger = get_logger("phase5")
os.makedirs(PHASE5_OUTPUT_DIR, exist_ok=True)

# ============================================================
# FOOD & BEVERAGE PRODUCT KEYWORD DETECTION
# ============================================================
FOOD_PRODUCT_KEYWORDS = [
    'tea', 'coffee', 'juice', 'drink', 'beverage', 'lassi', 'buttermilk',
    'coconut water', 'energy drink', 'smoothie', 'shake', 'soft drink',
    'milk', 'paneer', 'ghee', 'butter', 'cheese', 'curd', 'yogurt',
    'cream', 'dairy', 'whey protein',
    'bread', 'cake', 'biscuit', 'cookie', 'chocolate', 'candy', 'sweet',
    'mithai', 'laddoo', 'barfi', 'halwa', 'gulab jamun', 'rasgulla',
    'confectionery', 'pastry', 'muffin', 'cupcake', 'bakery', 'toffee',
    'snack', 'namkeen', 'bhujia', 'chiwda', 'popcorn', 'chips',
    'farsan', 'gathiya', 'makhana', 'peanut snack',
    'pickle', 'ketchup', 'chutney', 'jam', 'sauce', 'paste',
    'mayonnaise', 'vinegar', 'mustard', 'dressing', 'achar',
    'edible oil', 'cooking oil', 'sunflower oil', 'mustard oil',
    'coconut oil', 'groundnut oil', 'olive oil', 'sesame oil',
    'rice bran oil', 'soybean oil', 'palm oil', 'canola oil',
    'frozen food', 'frozen meal', 'frozen vegetable', 'frozen fruit',
    'frozen chicken', 'frozen fish', 'frozen prawn',
    'instant food', 'ready to eat', 'ready-to-eat', 'rte food',
    'canned food', 'preserved food',
    'chicken cut', 'fresh chicken', 'mutton', 'lamb cut', 'fresh fish',
    'prawn', 'shrimp', 'seafood', 'tuna', 'salmon',
    'cigarette', 'cigar', 'tobacco product',
    'baby food', 'infant formula', 'baby cereal', 'baby puree',
    'protein powder', 'mass gainer', 'pre-workout supplement',
    'bcaa supplement', 'creatine supplement', 'sports drink',
    'electrolyte drink for athlete',
    'basmati rice', 'white rice', 'brown rice', 'rice variety',
    'wheat flour', 'atta', 'maida', 'besan', 'flour variety',
    'dal variety', 'lentil variety', 'pulse variety', 'chana',
    'rajma', 'moong', 'toor dal', 'urad dal',
    'turmeric', 'black pepper', 'cumin', 'coriander', 'cardamom',
    'cinnamon', 'clove', 'ginger powder', 'chilli powder',
    'masala', 'spice blend',
]

FOOD_SUBCATEGORY_MAP = [
    (['tea', 'coffee', 'beverage', 'drink', 'lassi', 'buttermilk',
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
    (['protein powder', 'mass gainer', 'pre-workout supplement',
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
# FIX A — Agriculture & Food Products leftover
# ============================================================
FIX_A_REMAP = {
    'Baking Ingredients': ('Food & Beverage', 'Bakery & Confectionery Products'),
    'Certification Services': ('Services & Support', 'Certification & Compliance Services'),
    'Excess Inventory': None,
    'Food Grade Packaging': ('Packaging & Printing', 'Food Grade Packaging'),
    'Food Processing Machinery': ('Machinery & Equipment', 'Food Processing Machinery'),
    'Gardening Tools': ('Tools & Hardware', 'Gardening Tools'),
    'Manufacturing Services': ('Services & Support', 'Contract Manufacturing Services'),
    'Poultry Farming Services': ('Services & Support', 'Agricultural & Farming Services'),
    'Sports Nutrition & Supplements': ('Health & Personal Care', 'Health Supplements & Vitamins'),
    'Tobacco & Smoking Products': ('Food & Beverage', 'Tobacco & Smoking Products'),
    'Training & Capacity Building': ('Services & Support', 'Training & Skill Development'),
}

# ============================================================
# FIX B — Remove Energy & Power
# ============================================================
FIX_B_ENERGY_REMAP = {
    'Biogas Plant Machinery': ('Machinery & Equipment', 'Renewable Energy Machinery'),
    'Solar Energy Monitoring Systems': ('Software & IT Solutions', 'IoT & Smart Building Software'),
    'Wind Turbine Commissioning': ('Services & Support', 'Engineering & Technical Services'),
}

# ============================================================
# FIX C — ERP overload reclassification
# ============================================================
FIX_C_PRODUCT_SUBCATEGORY = {
    'AR Game Development Platforms': 'Creative & Game Development Software',
    'AR/VR Multiplayer Game Platforms': 'Creative & Game Development Software',
    'Custom VR Environments': 'Creative & Game Development Software',
    'DJ Software & Licenses': 'Creative & Game Development Software',
    'Enterprise VR Platforms': 'Creative & Game Development Software',
    'Music Production Software': 'Creative & Game Development Software',
    'Online Gaming Subscription Cards': 'Creative & Game Development Software',
    'Retail & E-commerce VR Solutions': 'Creative & Game Development Software',
    'Streaming Software Licenses': 'Creative & Game Development Software',
    'VR App Development Services': 'Creative & Game Development Software',
    'VR Content Creation Software': 'Creative & Game Development Software',
    'VR Data Analytics Tools': 'Creative & Game Development Software',
    'VR Development Boards & SDKs': 'Creative & Game Development Software',
    'VR Game Titles & Software': 'Creative & Game Development Software',
    'VR Integration Services': 'Creative & Game Development Software',
    'VR Streaming Platforms': 'Creative & Game Development Software',
    'VR in Real Estate & Architecture': 'Creative & Game Development Software',
    'Virtual Esports Solutions': 'Creative & Game Development Software',
    'Virtual Reality Fitness Training': 'Creative & Game Development Software',
    'Virtual Reality for Education': 'Creative & Game Development Software',
    'Air Quality Monitoring Devices': 'IoT & Smart Building Software',
    'App-Based Monitoring Systems': 'IoT & Smart Building Software',
    'Battery Management Systems (BMS)': 'IoT & Smart Building Software',
    'Building Management System (BMS) Panels': 'IoT & Smart Building Software',
    'Cloud-Based Smart Building Platforms': 'IoT & Smart Building Software',
    'Cold Chain Temperature Monitoring Systems': 'IoT & Smart Building Software',
    'IoT Gateways & Controllers': 'IoT & Smart Building Software',
    'IoT Solutions For Smart Farming': 'IoT & Smart Building Software',
    'IoT-Based Cold Chain Management': 'IoT & Smart Building Software',
    'Smart Building Mobile Apps': 'IoT & Smart Building Software',
    'Smart CCTV Monitoring Systems': 'IoT & Smart Building Software',
    'Smart Grid Controllers': 'IoT & Smart Building Software',
    'Smart Lighting Control Systems': 'IoT & Smart Building Software',
    'Smart Meters (Water, Electricity, Gas)': 'IoT & Smart Building Software',
    'SCADA Software Licenses': 'IoT & Smart Building Software',
    'HVAC Automation Controls': 'IoT & Smart Building Software',
    'CRM & Sales Automation Tools': 'CRM & Sales Automation Software',
    'Customer Relationship Management (CRM) Software': 'CRM & Sales Automation Software',
    'Email Marketing & Automation Tools': 'CRM & Sales Automation Software',
    'Helpdesk & Support Ticketing Systems': 'CRM & Sales Automation Software',
    'Point of Sale (POS) Systems': 'CRM & Sales Automation Software',
    'Sales Analytics & Reporting Tools': 'CRM & Sales Automation Software',
    'Attendance & HRMS Software': 'HR & Payroll Software',
    'Biometric Attendance Systems': 'HR & Payroll Software',
    'HR & Payroll Management Software': 'HR & Payroll Software',
    'Payroll Software Solutions': 'HR & Payroll Software',
    'Time & Attendance Management Software': 'HR & Payroll Software',
    'Hospital Information Management Systems (HIMS)': 'Healthcare IT Software',
    'Medical Billing Software Solutions': 'Healthcare IT Software',
    'Cloud Storage & File Sharing Services': 'Cloud & Productivity Software',
    'Office Productivity Software (MS Office, Google Workspace)': 'Cloud & Productivity Software',
    'Project Management & Collaboration Tools': 'Cloud & Productivity Software',
    'Video Conferencing Software (Zoom, Teams, Webex)': 'Cloud & Productivity Software',
    'Workflow Automation Software': 'Cloud & Productivity Software',
    'Agri ERP Software Implementation': 'Industry-Specific Software',
    'Dealership Management Software': 'Industry-Specific Software',
    'Digital Vehicle Inspection Software': 'Industry-Specific Software',
    'Label Design Software': 'Industry-Specific Software',
}

FIX_C_PRODUCT_CATEGORY_DEST = {
    'Augmented Reality (AR) Toys': ('Home & Lifestyle', "Children's Play Equipment & Toys"),
    'Baby Monitors': ('Home & Lifestyle', "Children's Play Equipment & Toys"),
    'Electronic Board Games': ('Home & Lifestyle', "Children's Play Equipment & Toys"),
    'Electronic Building Blocks': ('Home & Lifestyle', "Children's Play Equipment & Toys"),
    'Language Learning Devices': ('Home & Lifestyle', "Children's Play Equipment & Toys"),
    'Musical Toys': ('Home & Lifestyle', "Children's Play Equipment & Toys"),
    'Box Build Assembly': ('Electrical & Electronics', 'PCB & Electronic Components'),
    'Conformal Coating Services': ('Electrical & Electronics', 'PCB & Electronic Components'),
    'High Volume PCB Assembly': ('Electrical & Electronics', 'PCB & Electronic Components'),
    'PCB Soldering Services': ('Electrical & Electronics', 'PCB & Electronic Components'),
    'Prototype PCB Assembly': ('Electrical & Electronics', 'PCB & Electronic Components'),
    'Turnkey PCB Assembly Services': ('Electrical & Electronics', 'PCB & Electronic Components'),
    'Barcode Labels For Waste Bags': ('Packaging & Printing', 'Barcode Labels & RFID Tags'),
    'Lighting Design Consultants': ('Services & Support', 'Engineering & Technical Services'),
    'Operator Training Programs': ('Services & Support', 'Training & Skill Development'),
}

# ============================================================
# FIX D — Invalid software subcategory names
# ============================================================
FIX_D_SUBCATEGORY_RENAME = {
    'Electronic Components': 'Industry-Specific Software',
    'Fleet Management Solutions': 'Industry-Specific Software',
    'Medical Consumables': 'Healthcare IT Software',
    'Packaging Materials': 'Industry-Specific Software',
    'Retail Point of Sale (POS) Software': 'CRM & Sales Automation Software',
    'Healthcare IT Solutions': 'Healthcare IT Software',
    'Embedded Systems Development': 'Industry-Specific Software',
}

# ============================================================
# FIX SW — Move non-software subcategories out of Software
# ============================================================
SW_WRONG_SUBCATEGORIES = {
    'Electronic Assembly Services': ('Electrical & Electronics', 'PCB & Electronic Components'),
    'Computers, Laptops & Peripherals': ('Electrical & Electronics', 'Computers, Laptops & Peripherals'),
    'Electronic Component Repair & Maintenance Services': ('Services & Support', 'IT Support & Managed Services'),
    'Electronic Design & Prototyping Services': ('Services & Support', 'Engineering & Technical Services'),
    'Retail Point of Sale (POS) Systems': ('Software & IT Solutions', 'CRM & Sales Automation Software'),
    'Ambulance Fleet Management Software': ('Software & IT Solutions', 'Healthcare IT Software'),
    'Mental Health & Wellness Applications': ('Software & IT Solutions', 'Healthcare IT Software'),
    'Gaming Software & Platforms': ('Software & IT Solutions', 'Creative & Game Development Software'),
    'Enterprise Resource Planning (ERP) Systems': ('Software & IT Solutions', 'ERP & Business Management Software'),
}

# ============================================================
# FIX E — Sports construction products
# ============================================================
FIX_E_SPORTS_CONSTRUCTION = {
    'Badminton Court Construction': ('Construction & Infrastructure', 'Sports & Recreational Infrastructure'),
    'Basketball Court Construction': ('Construction & Infrastructure', 'Sports & Recreational Infrastructure'),
    'Cricket Ground Development': ('Construction & Infrastructure', 'Sports & Recreational Infrastructure'),
    'Football Field Construction': ('Construction & Infrastructure', 'Sports & Recreational Infrastructure'),
    'Indoor Sports Hall Construction': ('Construction & Infrastructure', 'Sports & Recreational Infrastructure'),
    'Swimming Pool Construction': ('Construction & Infrastructure', 'Sports & Recreational Infrastructure'),
    'Tennis Court Construction': ('Construction & Infrastructure', 'Sports & Recreational Infrastructure'),
    'Stadium Seating Installation': ('Construction & Infrastructure', 'Sports & Recreational Infrastructure'),
    'Sports Flooring Installation (Pvc, Wooden, Pu)': ('Construction & Infrastructure', 'Tiles, Marble, Granite & Flooring'),
    'Sports Lighting Systems': ('Electrical & Electronics', 'Lighting Fixtures & Fittings'),
    'Gym And Fitness Center Setup': ('Services & Support', 'Engineering & Technical Services'),
}

# ============================================================
# SPECIFIC CATEGORY/SUBCATEGORY FIXES
# ============================================================
SPECIFIC_FIXES = {
    ('Apparel & Fashion', 'Retail Point of Sale (POS) Software'): ('Software & IT Solutions', 'CRM & Sales Automation Software'),
    ('Chemicals & Raw Materials', 'PCB & Electronic Components'): ('Electrical & Electronics', 'PCB & Electronic Components'),
    ('Chemicals & Raw Materials', 'Excess Inventory'): None,
    ('Machinery & Equipment', 'Excess Inventory'): None,
    ('Chemicals & Raw Materials', 'Certification Services'): ('Services & Support', 'Certification & Compliance Services'),
    ('Home & Lifestyle', 'Engineering & Technical Services'): ('Services & Support', 'Engineering & Technical Services'),
    ('Machinery & Equipment', 'Engineering & Technical Services'): ('Services & Support', 'Engineering & Technical Services'),
    ('Machinery & Equipment', 'PCB & Electronic Components'): ('Electrical & Electronics', 'PCB & Electronic Components'),
    ('Machinery & Equipment', 'Medical Waste Disposal Products'): ('Health & Personal Care', 'Medical Consumables'),
    ('Health & Personal Care', 'Healthcare IT Solutions'): ('Software & IT Solutions', 'Healthcare IT Software'),
    ('Electrical & Electronics', 'Healthcare IT Solutions'): ('Software & IT Solutions', 'Healthcare IT Software'),
    ('Machinery & Equipment', 'Healthcare IT Solutions'): ('Software & IT Solutions', 'Healthcare IT Software'),
    ('Electrical & Electronics', 'Engineering & Technical Services'): ('Services & Support', 'Engineering & Technical Services'),
    ('Services & Support', 'Excess Inventory Management'): None,
    ('Agriculture & Food Products', 'Excess Inventory'): None,
}

PRODUCTS_TO_DELETE = {
    'Farm Tool &', 'Wood &', 'Exporters of Agri Equipment',
    'ODM Tool', 'Equipment', 'Farm Equipment',
}

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

def run():
    if is_completed('phase5'):
        return

    logger.info('Starting Phase 5 — Validator v7 (Complete)')

    input_path = os.path.join(PHASE4_OUTPUT_DIR, 'normalized.csv')
    if not os.path.exists(input_path):
        raise FileNotFoundError(f'Phase 4 output not found: {input_path}')

    df = pd.read_csv(input_path)
    if 'attributes' in df.columns:
        df = df.drop(columns=['attributes'])

    initial = len(df)
    logger.info(f'Input rows: {initial}')
    rows_to_delete = []

    # ── PRE-FIX: Rename Agriculture & Food Products → Agriculture & Farming
    afp_mask = df['category'] == 'Agriculture & Food Products'
    df.loc[afp_mask, 'category'] = 'Agriculture & Farming'
    logger.info(f'Renamed Agriculture & Food Products → Agriculture & Farming: {afp_mask.sum()} rows')

    # ── PRE-FIX 2: Delete Excess Inventory subcategory
    excess_mask = df['subcategory'] == 'Excess Inventory'
    rows_to_delete.extend(df[excess_mask].index.tolist())
    logger.info(f'Marked {excess_mask.sum()} Excess Inventory rows for deletion')

    # ── ISSUE 9: Delete truncated/invalid products
    delete_mask = df['product_category'].isin(PRODUCTS_TO_DELETE)
    rows_to_delete.extend(df[delete_mask].index.tolist())
    logger.info(f'Issue 9: Marked {delete_mask.sum()} truncated/invalid products for deletion')

    # ── ISSUE 1: Food & Beverage keyword-based split
    food_found = 0
    for idx, row in df.iterrows():
        if idx in rows_to_delete:
            continue
        prod = str(row['product_category'])
        if is_food_product(prod):
            if row['category'] not in ('Food & Beverage', 'Health & Personal Care',
                                        'Packaging & Printing', 'Services & Support'):
                sub = get_food_subcategory(prod)
                df.at[idx, 'category'] = 'Food & Beverage'
                df.at[idx, 'subcategory'] = sub
                food_found += 1
    logger.info(f'Issue 1: Moved {food_found} food products to Food & Beverage')

    # ── FIX A: Agriculture & Food Products leftover
    afp_mask2 = df['category'] == 'Agriculture & Food Products'
    for idx, row in df[afp_mask2].iterrows():
        dest = FIX_A_REMAP.get(row['subcategory'])
        if dest is None:
            rows_to_delete.append(idx)
        else:
            df.at[idx, 'category'] = dest[0]
            df.at[idx, 'subcategory'] = dest[1]

    # ── FIX B: Remove Energy & Power
    energy_mask = df['category'] == 'Energy & Power'
    for idx, row in df[energy_mask].iterrows():
        new_cat, new_sub = FIX_B_ENERGY_REMAP.get(
            row['product_category'], ('Electrical & Electronics', 'Renewable Energy Equipment'))
        df.at[idx, 'category'] = new_cat
        df.at[idx, 'subcategory'] = new_sub
    logger.info(f'Fix B: Energy & Power eliminated ({energy_mask.sum()} products remapped)')

    # ── FIX C: ERP overload reclassification
    erp_mask = ((df['category'] == 'Software & IT Solutions') &
                (df['subcategory'] == 'ERP & Business Management Software'))
    erp_reclassified = 0
    for idx, row in df[erp_mask].iterrows():
        prod = row['product_category']
        if prod in FIX_C_PRODUCT_SUBCATEGORY:
            df.at[idx, 'subcategory'] = FIX_C_PRODUCT_SUBCATEGORY[prod]
            erp_reclassified += 1
        elif prod in FIX_C_PRODUCT_CATEGORY_DEST:
            new_cat, new_sub = FIX_C_PRODUCT_CATEGORY_DEST[prod]
            df.at[idx, 'category'] = new_cat
            df.at[idx, 'subcategory'] = new_sub
            erp_reclassified += 1
    logger.info(f'Fix C: ERP reclassification — {erp_reclassified} products moved')

    # ── FIX D: Rename invalid software subcategories
    sw_mask = df['category'] == 'Software & IT Solutions'
    for idx, row in df[sw_mask].iterrows():
        if row['subcategory'] in FIX_D_SUBCATEGORY_RENAME:
            df.at[idx, 'subcategory'] = FIX_D_SUBCATEGORY_RENAME[row['subcategory']]
    logger.info('Fix D: Invalid software subcategory names corrected')

    # ── FIX SW: Move non-software subcategories out of Software
    sw_fix_count = 0
    for idx, row in df[df['category'] == 'Software & IT Solutions'].iterrows():
        if row['subcategory'] in SW_WRONG_SUBCATEGORIES:
            new_cat, new_sub = SW_WRONG_SUBCATEGORIES[row['subcategory']]
            df.at[idx, 'category'] = new_cat
            df.at[idx, 'subcategory'] = new_sub
            sw_fix_count += 1
    logger.info(f'Fix SW: {sw_fix_count} products moved out of wrong Software subcategories')

    # ── FIX E: Sports construction products
    sports_eng_mask = ((df['category'] == 'Sports & Entertainment') &
                       (df['subcategory'] == 'Engineering & Technical Services'))
    for idx, row in df[sports_eng_mask].iterrows():
        new_cat, new_sub = FIX_E_SPORTS_CONSTRUCTION.get(
            row['product_category'],
            ('Construction & Infrastructure', 'Sports & Recreational Infrastructure'))
        df.at[idx, 'category'] = new_cat
        df.at[idx, 'subcategory'] = new_sub
    logger.info(f'Fix E: {sports_eng_mask.sum()} sports construction products moved')

    # ── SPECIFIC FIXES (issues 3-8)
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
    logger.info(f'Specific fixes: {specific_fixed} fixed, {specific_deleted} deleted')

    # ── ISSUE 2: Industrial Tools split
    it_mask = ((df['category'] == 'Machinery & Equipment') &
               (df['subcategory'] == 'Industrial Tools'))
    it_packaging_kw = ['shrink wrap', 'packing machine', 'filling machine', 'sealing machine',
        'labeling machine', 'cartoning', 'form fill seal', 'wrapping machine', 'packaging line',
        'case packer', 'coding machine', 'flow wrap', 'sleeve wrap', 'auger fill',
        'bag in box', 'pouch packing', 'sachet pack', 'induction seal', 'carton sealer',
        'foil wrap machine', 'vacuum packing', 'multi-lane pack', 'heat sealing machine']
    it_metal_kw = ['scrap metal', 'metal scrap', 'steel scrap', 'copper scrap', 'aluminum scrap',
        'iron scrap', 'metal coil', 'metal rod', 'stainless steel sheet', 'metal plate',
        'steel plate', 'aluminum plate', 'metal foil', 'metal baling', 'ferrous scrap',
        'non-ferrous scrap', 'metal turnings', 'cast iron scrap']
    it_cold_kw = ['cold room', 'cold storage unit', 'refrigerated van', 'reefer container',
        'portable cold box', 'insulated delivery box', 'condensing unit']
    it_stage_kw = ['stage platform', 'stage riser', 'stage truss', 'dj booth', 'pipe and drape',
        'backdrop frame', 'stage canopy', 'stage curtain', 'portable stage', 'studio furniture']
    it_farm_kw = ['seed dibbler', 'seed grader', 'direct seeder', 'soil auger', 'nursery seedling',
        'agricultural crate', 'farm trailer', 'fertilizer spreader', 'transplanter', 'brush cutter',
        'polyhouse', 'venturi injector']
    it_apparel_kw = ['garment sample', 'apparel cad', 'fit sample', 'fabric swatch',
        'embroidery sample', 'pre-production sample', 'pattern testing', 'colorway sample']
    it_reclassified = 0
    for idx, row in df[it_mask].iterrows():
        prod = row['product_category'].lower()
        if any(kw in prod for kw in it_packaging_kw):
            df.at[idx, 'subcategory'] = 'Packaging Machinery'
            it_reclassified += 1
        elif any(kw in prod for kw in it_metal_kw):
            df.at[idx, 'category'] = 'Chemicals & Raw Materials'
            df.at[idx, 'subcategory'] = 'Scrap Metals & Recycled Alloys'
            it_reclassified += 1
        elif any(kw in prod for kw in it_cold_kw):
            df.at[idx, 'subcategory'] = 'Cold Chain & Refrigeration Equipment'
            it_reclassified += 1
        elif any(kw in prod for kw in it_stage_kw):
            df.at[idx, 'category'] = 'Sports & Entertainment'
            df.at[idx, 'subcategory'] = 'Stage, Set & Truss Equipment'
            it_reclassified += 1
        elif any(kw in prod for kw in it_farm_kw):
            df.at[idx, 'subcategory'] = 'Agricultural Machinery'
            it_reclassified += 1
        elif any(kw in prod for kw in it_apparel_kw):
            df.at[idx, 'category'] = 'Apparel & Fashion'
            df.at[idx, 'subcategory'] = 'Garment Accessories & Trims'
            it_reclassified += 1
    logger.info(f'Issue 2: Industrial Tools split — {it_reclassified} products reclassified')

    # ── ERP keyword reclassification
    erp_mask2 = ((df['category'] == 'Software & IT Solutions') &
                 (df['subcategory'] == 'ERP & Business Management Software'))
    iot_kw = ['air quality monitor', 'app-based monitoring', 'battery management system',
        'building management system', 'cloud-based smart building', 'cold chain temperature',
        'data logger', 'iot gateway', 'iot solutions for smart', 'iot-based cold',
        'iot-enabled', 'leak detection', 'motorized curtain', 'occupancy sensor',
        'power factor correction', 'remote lock', 'scada', 'smart building mobile',
        'smart cctv', 'smart grid', 'smart lighting control', 'smart meter',
        'smart video door', 'wi-fi & bluetooth smart', 'wireless control system', 'zigbee',
        'hvac automation', 'integrated facility dashboard']
    crm_kw = ['crm & sales', 'customer relationship management', 'crm software',
        'email marketing', 'helpdesk & support ticketing', 'loyalty program integrated pos',
        'marketplace order sync', 'mobile pos apps', 'pos integration for fashion',
        'pos with whatsapp', 'point of sale', 'return & exchange management',
        'saas subscription pos', 'sales analytics', 'cloud-based fashion pos', 'custom fashion pos']
    hr_kw = ['attendance & hrms', 'biometric attendance', 'hr & payroll management',
        'hrms & payroll', 'human resource management systems', 'payroll software',
        'time & attendance management']
    health_kw = ['cloud-based medical transcription', 'diagnostic software & scanner',
        'hospital information management', 'medical billing software', 'medical vr equipment',
        'healthcare startup']
    industry_kw = ['adulteration detection', 'agri erp software', 'allergen testing',
        'automated optical inspection', 'cnc cutting software', 'chemical process control',
        'crop protection monitoring', 'dealership management', 'digital vehicle inspection',
        'export documentation & compliance', 'fssai compliance', 'face recognition access',
        'farm automation', 'hmi control', 'halal, kosher testing', 'heavy metal analysis',
        'iso 22000', 'label claim validation', 'label design software',
        'microbiological testing', 'nutritional analysis', 'organic certification testing',
        'plc integrated', 'shelf life & stability', 'tech pack to sample',
        'ux/ui design for infotainment', 'vibration monitoring for bearings',
        'waste tracking logs', 'water quality testing for food', 'cad & 3d design software']
    cloud_kw = ['accounting & billing software', 'accounting & bookkeeping saas',
        'accounting software (tally', 'agile & scrum', 'api development & integration',
        'automated billing & invoicing', 'cloud storage', 'compliance checklist',
        'desktop application development', 'developer tools',
        'document management & e-signature', 'electronic signature software',
        'encrypted file transmission', 'hybrid event solutions', 'id card design software',
        'laptop & desktop leasing', 'network & it tool', 'office productivity software',
        'operating system licenses', 'post-implementation support', 'project management',
        'saas product development', 'secure document sharing',
        'smartwatch app development', 'software development consulting',
        'software maintenance & support', 'speech recognition ai',
        'task management & reminder', 'video conferencing software', 'virtual classrooms',
        'virtual event management', 'virtual group classes', 'voice recognition toys',
        'web application development', 'website & landing page', 'workflow automation']
    creative_kw = ['ar game development', 'ar/vr multiplayer', 'custom vr environment',
        'dj software', 'enterprise vr platform', 'music production software',
        'online gaming subscription', 'retail & e-commerce vr', 'streaming software license',
        'vr app development', 'vr content creation', 'vr data analytics',
        'vr development boards', 'vr game title', 'vr integration services',
        'vr streaming', 'vr in real estate', 'virtual esports', 'virtual reality fitness',
        'virtual reality for education']
    toys_kw = ['augmented reality (ar) toy', 'baby monitor', 'digital flashcard',
        'electronic board game', 'electronic building block', 'electronic drawing pad',
        'language learning device', 'musical toy', 'remote-controlled educational',
        'sound and light toy']
    pcb_kw = ['box build assembly', 'conformal coating service', 'custom electronic assembly',
        'high volume pcb', 'mixed technology assembly', 'pcb soldering', 'pcba testing',
        'prototype pcb', 'reflow soldering', 'surface mount technology',
        'through-hole assembly', 'turnkey pcb', 'wave soldering', 'x-ray inspection for pcb']

    erp_reclassified2 = 0
    for idx, row in df[erp_mask2].iterrows():
        prod = row['product_category'].lower()
        if any(kw in prod for kw in iot_kw):
            df.at[idx, 'subcategory'] = 'IoT & Smart Building Software'
            erp_reclassified2 += 1
        elif any(kw in prod for kw in crm_kw):
            df.at[idx, 'subcategory'] = 'CRM & Sales Automation Software'
            erp_reclassified2 += 1
        elif any(kw in prod for kw in hr_kw):
            df.at[idx, 'subcategory'] = 'HR & Payroll Software'
            erp_reclassified2 += 1
        elif any(kw in prod for kw in health_kw):
            df.at[idx, 'subcategory'] = 'Healthcare IT Software'
            erp_reclassified2 += 1
        elif any(kw in prod for kw in industry_kw):
            df.at[idx, 'subcategory'] = 'Industry-Specific Software'
            erp_reclassified2 += 1
        elif any(kw in prod for kw in cloud_kw):
            df.at[idx, 'subcategory'] = 'Cloud & Productivity Software'
            erp_reclassified2 += 1
        elif any(kw in prod for kw in creative_kw):
            df.at[idx, 'subcategory'] = 'Creative & Game Development Software'
            erp_reclassified2 += 1
        elif any(kw in prod for kw in toys_kw):
            df.at[idx, 'category'] = 'Home & Lifestyle'
            df.at[idx, 'subcategory'] = "Children's Play Equipment & Toys"
            erp_reclassified2 += 1
        elif any(kw in prod for kw in pcb_kw):
            df.at[idx, 'category'] = 'Electrical & Electronics'
            df.at[idx, 'subcategory'] = 'PCB & Electronic Components'
            erp_reclassified2 += 1
    logger.info(f'ERP keyword reclassification: {erp_reclassified2} products moved')

    # ── APPLY DELETIONS
    df = df.drop(index=list(set(rows_to_delete)))
    logger.info(f'Total rows deleted: {len(set(rows_to_delete))}')

    # ── SOFTWARE MISPLACEMENT
    misplaced_mask = df.apply(
        lambda row: row['category'] in NON_SOFTWARE_CATEGORIES
                    and is_software(str(row['product_category'])), axis=1)
    if misplaced_mask.sum():
        logger.warning(f'Misplaced software auto-corrected: {misplaced_mask.sum()}')
        df.loc[misplaced_mask, 'category'] = 'Software & IT Solutions'
        df.loc[misplaced_mask, 'subcategory'] = 'Industry-Specific Software'

    # ── DEDUPLICATION
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

    # ── DROP EMPTY
    df = df.dropna(subset=['category', 'subcategory', 'product_category'])
    df = df[df['product_category'].str.strip() != '']

    # ── SORT
    df = df.sort_values(['category', 'subcategory', 'product_category']).reset_index(drop=True)

    final = len(df)
    cat_count = df['category'].nunique()
    sub_count = df['subcategory'].nunique()

    # ── VALIDATION REPORT
    food_bev = len(df[df['category'] == 'Food & Beverage'])
    agri = len(df[df['category'] == 'Agriculture & Farming'])
    it_remaining = len(df[(df['category'] == 'Machinery & Equipment') &
                          (df['subcategory'] == 'Industrial Tools')])
    hc_it_wrong = len(df[df['subcategory'] == 'Healthcare IT Solutions'])
    excess = len(df[df['subcategory'] == 'Excess Inventory'])
    sw_subs = df[df['category'] == 'Software & IT Solutions']['subcategory'].value_counts()

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
