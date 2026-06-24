import os
import re
import pandas as pd
from common.config import PHASE4_OUTPUT_DIR, PHASE5_OUTPUT_DIR
from common.logger import get_logger
from common.checkpoint import is_completed, mark_completed
from common.metrics import set_metric, save_metrics

logger = get_logger("phase5")

os.makedirs(PHASE5_OUTPUT_DIR, exist_ok=True)

# ============================================================
# FIX 1 — TRUNCATED PRODUCT NAMES
# Products ending with & or connector words
# ============================================================
def is_truncated(name: str) -> bool:
    stripped = name.strip()
    if stripped.endswith('&') or stripped.endswith('And') or stripped.endswith(','):
        return True
    if re.search(r'\s&\s*$', stripped):
        return True
    # Garbled Qwen outputs
    garbled = ['hips', 'EVhips', 'Wheelerhips', 'Bikehips', 'Carhips']
    if any(g.lower() in stripped.lower() for g in garbled):
        return True
    return False

# ============================================================
# FIX 1 — TOO GENERIC / TOO SHORT PRODUCT NAMES
# ============================================================
GENERIC_PRODUCT_NAMES = {
    'apparel', 'software', 'services', 'products', 'equipment',
    'materials', 'tools', 'systems', 'bag', 'footwear', 'garment',
    'jewelry', 'shoe', 'belt', 'swimwear', 'beverage', 'dairy',
    'fertilizer', 'sauce', 'snack', 'ingredients', 'equipment',
    'perfume', 'press', 'drinkware', 'lubricants', 'battery',
}

def is_too_generic(name: str) -> bool:
    return name.lower().strip() in GENERIC_PRODUCT_NAMES

# ============================================================
# FIX 2 — BUSINESS ENTITY PRODUCT NAMES
# ============================================================
BUSINESS_ENTITY_PATTERNS = [
    r'\bauthorized\b',
    r'\bcontractors?\b',
    r'\bsolution providers?\b',
    r'\bintegrators?\b',
    r'\bstockists?\b',
    r'\bdealers?\s+&\s+distributors?\b',
    r'\bbuyers?\s+&\b',
    r'\binsulation contractors?\b',
    r'\bacoustic solution providers?\b',
]

def is_business_entity_product(name: str) -> bool:
    lower = name.lower()
    for pattern in BUSINESS_ENTITY_PATTERNS:
        if re.search(pattern, lower):
            return True
    return False

# ============================================================
# FIX 3 — SUBCATEGORY = PRODUCT CATEGORY (REDUNDANT)
# ============================================================
def is_redundant_entry(row) -> bool:
    return row['subcategory'].strip().lower() == row['product_category'].strip().lower()

# ============================================================
# FIX 5 — SPLIT APPAREL MANAGEMENT SOFTWARE SUBCATEGORY
# ============================================================
AMS_SUBCATEGORY_MAP = {
    # Apparel & Fashion ERP
    'apparel inventory': 'Apparel & Fashion ERP Software',
    'apparel dropshipping': 'Apparel & Fashion ERP Software',
    'apparel business intelligence': 'Apparel & Fashion ERP Software',
    'cloud-based apparel erp': 'Apparel & Fashion ERP Software',
    'custom erp for fashion': 'Apparel & Fashion ERP Software',
    'fashion design & development erp': 'Apparel & Fashion ERP Software',
    'garment manufacturing erp': 'Apparel & Fashion ERP Software',
    'mobile erp solutions for apparel': 'Apparel & Fashion ERP Software',
    'multi-warehouse apparel': 'Apparel & Fashion ERP Software',
    'multi-channel retail erp': 'Apparel & Fashion ERP Software',
    'production status monitoring erp': 'Apparel & Fashion ERP Software',
    'raw material management erp': 'Apparel & Fashion ERP Software',
    'stock replenishment & forecasting': 'Apparel & Fashion ERP Software',
    'textile production erp': 'Apparel & Fashion ERP Software',
    'vendor management software for apparel': 'Apparel & Fashion ERP Software',
    'textile cad': 'Apparel & Fashion ERP Software',
    'pos integration for fashion': 'Apparel & Fashion ERP Software',
    'erp software development': 'Apparel & Fashion ERP Software',
    'enterprise software solutions': 'Apparel & Fashion ERP Software',

    # HR & Payroll
    'attendance & hrms': 'HR & Payroll Software',
    'biometric attendance': 'HR & Payroll Software',
    'hr & payroll management': 'HR & Payroll Software',
    'hrms & payroll': 'HR & Payroll Software',
    'human resource management systems': 'HR & Payroll Software',
    'payroll software': 'HR & Payroll Software',
    'time & attendance management': 'HR & Payroll Software',

    # CRM & Sales
    'crm & sales automation': 'CRM & Sales Automation Software',
    'crm software development': 'CRM & Sales Automation Software',
    'email marketing & automation': 'CRM & Sales Automation Software',
    'email marketing software': 'CRM & Sales Automation Software',
    'helpdesk & support ticketing': 'CRM & Sales Automation Software',

    # IoT & Smart Building
    'building management system': 'IoT & Smart Building Software',
    'cloud-based smart building': 'IoT & Smart Building Software',
    'hvac automation': 'IoT & Smart Building Software',
    'home & building voice': 'IoT & Smart Building Software',
    'iot gateways': 'IoT & Smart Building Software',
    'iot solutions for smart farming': 'IoT & Smart Building Software',
    'iot-enabled': 'IoT & Smart Building Software',
    'motorized curtain': 'IoT & Smart Building Software',
    'occupancy sensors': 'IoT & Smart Building Software',
    'power factor correction': 'IoT & Smart Building Software',
    'remote lock': 'IoT & Smart Building Software',
    'smart building mobile': 'IoT & Smart Building Software',
    'smart cctv monitoring': 'IoT & Smart Building Software',
    'smart grid': 'IoT & Smart Building Software',
    'smart meters': 'IoT & Smart Building Software',
    'smart yoga devices': 'IoT & Smart Building Software',
    'wi-fi & bluetooth smart': 'IoT & Smart Building Software',
    'wireless control systems': 'IoT & Smart Building Software',
    'zigbee': 'IoT & Smart Building Software',
    'custom automation software': 'IoT & Smart Building Software',

    # Cloud & Productivity
    'cloud storage': 'Cloud & Productivity Software',
    'desktop application development': 'Cloud & Productivity Software',
    'developer tools': 'Cloud & Productivity Software',
    'document management & e-signature': 'Cloud & Productivity Software',
    'laptop & desktop leasing': 'Cloud & Productivity Software',
    'office productivity software': 'Cloud & Productivity Software',
    'operating system licenses': 'Cloud & Productivity Software',
    'project management & collaboration': 'Cloud & Productivity Software',
    'saas product development': 'Cloud & Productivity Software',
    'video conferencing software': 'Cloud & Productivity Software',
    'web application development': 'Cloud & Productivity Software',
    'website & landing page': 'Cloud & Productivity Software',
}

def get_ams_subcategory(product_name: str) -> str:
    lower = product_name.lower()
    for keyword, subcategory in AMS_SUBCATEGORY_MAP.items():
        if keyword in lower:
            return subcategory
    return 'Enterprise & Business Software'

# ============================================================
# FIX 6 — ENERGY & POWER CATEGORY
# ============================================================
ENERGY_KEYWORDS = [
    'solar panel', 'solar energy', 'solar power', 'photovoltaic', 'pv module',
    'wind turbine', 'wind energy', 'wind power',
    'ev charging', 'electric vehicle charging', 'ev charger',
    'biomass energy', 'hydropower', 'tidal energy', 'geothermal',
    'fuel cell', 'hydrogen energy', 'biogas plant',
    'power plant equipment', 'turbine generator',
    'energy storage system', 'battery energy storage',
    'renewable energy', 'smart grid', 'solar inverter',
    'solar water heater', 'solar street light', 'solar pump',
    'wind farm', 'offshore wind',
]

ENERGY_SUBCATEGORY_MAP = {
    'solar panel': 'Solar Energy Products',
    'solar energy': 'Solar Energy Products',
    'solar power': 'Solar Energy Products',
    'photovoltaic': 'Solar Energy Products',
    'pv module': 'Solar Energy Products',
    'solar inverter': 'Solar Energy Products',
    'solar water heater': 'Solar Energy Products',
    'solar street light': 'Solar Energy Products',
    'solar pump': 'Solar Energy Products',
    'wind turbine': 'Wind Energy Products',
    'wind energy': 'Wind Energy Products',
    'wind power': 'Wind Energy Products',
    'wind farm': 'Wind Energy Products',
    'offshore wind': 'Wind Energy Products',
    'ev charging': 'EV Charging Infrastructure',
    'electric vehicle charging': 'EV Charging Infrastructure',
    'ev charger': 'EV Charging Infrastructure',
    'biomass': 'Biomass & Bioenergy',
    'biogas': 'Biomass & Bioenergy',
    'fuel cell': 'Hydrogen & Fuel Cells',
    'hydrogen energy': 'Hydrogen & Fuel Cells',
    'energy storage': 'Energy Storage Systems',
    'battery energy storage': 'Energy Storage Systems',
    'smart grid': 'Smart Grid & Energy Management',
    'renewable energy': 'Renewable Energy Solutions',
    'hydropower': 'Hydro & Tidal Energy',
    'tidal energy': 'Hydro & Tidal Energy',
    'geothermal': 'Geothermal Energy',
    'power plant': 'Power Generation Equipment',
    'turbine generator': 'Power Generation Equipment',
}

def is_energy_product(name: str) -> bool:
    lower = name.lower()
    return any(kw in lower for kw in ENERGY_KEYWORDS)

def get_energy_subcategory(name: str) -> str:
    lower = name.lower()
    for kw, sub in ENERGY_SUBCATEGORY_MAP.items():
        if kw in lower:
            return sub
    return 'Renewable Energy Solutions'

# ============================================================
# FIX 7 — FOOD & BEVERAGE SEPARATION
# ============================================================
FOOD_BEVERAGE_SUBCATEGORIES = {
    'Beverages (Tea, Coffee, Juices)',
    'Bakery & Confectionery Products',
    'Snacks & Namkeens',
    'Condiments & Sauces',
    'Canned & Preserved Foods',
    'Frozen & Processed Foods',
    'Ready-to-Eat & Instant Foods',
    'Dairy Products & Alternatives',
    'Meat, Poultry & Seafood',
    'Edible Oils & Fats',
    'Baby Food Products',
    'Health & Nutritional Foods',
    'Catering Supplies & Ingredients',
    'Food Additives & Preservatives',
    'Flour, Sugar, Salt & Other Essentials',
}

AGRICULTURE_SUBCATEGORIES = {
    'Seeds & Planting Materials',
    'Fertilizers & Soil Conditioners',
    'Pesticides & Crop Protection',
    'Agricultural Equipment & Implements',
    'Agricultural Produce',
    'Organic Produce',
    'Grains, Cereals & Pulses',
    'Beekeeping Supplies',
    'Livestock Farming Equipment',
    'Poultry Farming Equipment',
    'Aquaculture & Fisheries Equipment',
    'Irrigation Systems & Equipment',
    'Hydroponic & Vertical Farming Systems',
    'Agricultural Consultancy Services',
    'Organic Farming Supplies',
    'Cold Chain Logistics & Storage',
    'Food Testing & Quality Control Services',
    'Agricultural Machinery',
    'Fresh Fruits & Vegetables',
    'Spices & Herbs',
    'Animal Feed & Nutrition',
}

def get_food_vs_agri_category(subcategory: str, product: str) -> str:
    if subcategory in FOOD_BEVERAGE_SUBCATEGORIES:
        return 'Food & Beverage'
    if subcategory in AGRICULTURE_SUBCATEGORIES:
        return 'Agriculture & Farming'
    # Default — keep original
    return 'Agriculture & Food Products'

# ============================================================
# SOFTWARE DETECTION (refined)
# ============================================================
NON_SOFTWARE_CATEGORIES = {
    'Apparel & Fashion', 'Agriculture & Food Products', 'Agriculture & Farming',
    'Food & Beverage', 'Machinery & Equipment', 'Chemicals & Raw Materials',
    'Electrical & Electronics', 'Construction & Infrastructure',
    'Health & Personal Care', 'Automotive & Transport', 'Home & Lifestyle',
    'Tools & Hardware', 'Packaging & Printing', 'Office Supplies & Equipment',
    'Sports & Entertainment', 'Energy & Power',
}

SOFTWARE_KEYWORDS = [
    'software', 'erp', 'crm', 'saas', 'management system',
    'tracking system', 'automation system', 'information system',
    'management platform', 'analytics platform',
]

PHYSICAL_WHITELIST = [
    'platform bed', 'platform scale', 'platform ladder', 'platform lift',
    'platform shoe', 'platform rental', 'scissor lift', 'dashboard cover',
    'dashboard organizer', 'dashboard polish', 'dashboard lighting',
    'dashboard component', 'dashboard & instrument', 'smart bulb',
    'smart thermometer', 'alarm system', 'building management system',
    'grout filling', 'sealant application', 'organic dye', 'home lift',
    'automation system installation', 'fleet tracking', 'platform ladder',
]

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

    logger.info('Starting Phase 5 — Validator v3')

    input_path = os.path.join(PHASE4_OUTPUT_DIR, 'normalized.csv')
    if not os.path.exists(input_path):
        raise FileNotFoundError(f'Phase 4 output not found: {input_path}')

    df = pd.read_csv(input_path)
    initial = len(df)
    logger.info(f'Input rows: {initial}')

    issues = []

    # ── FIX 1A: Remove truncated product names ──────────────────
    truncated_mask = df['product_category'].apply(is_truncated)
    truncated_count = truncated_mask.sum()
    if truncated_count:
        logger.info(f'Fix 1A: Removing {truncated_count} truncated product names')
        for prod in df[truncated_mask]['product_category'].tolist():
            issues.append(f'REMOVED_TRUNCATED: {prod}')
    df = df[~truncated_mask]

    # ── FIX 1B: Remove too-generic single-word products ─────────
    generic_mask = df['product_category'].apply(is_too_generic)
    generic_count = generic_mask.sum()
    if generic_count:
        logger.info(f'Fix 1B: Removing {generic_count} too-generic product names')
        for prod in df[generic_mask]['product_category'].tolist():
            issues.append(f'REMOVED_GENERIC: {prod}')
    df = df[~generic_mask]

    # ── FIX 2: Remove business entity product names ─────────────
    biz_mask = df['product_category'].apply(is_business_entity_product)
    biz_count = biz_mask.sum()
    if biz_count:
        logger.info(f'Fix 2: Removing {biz_count} business entity product names')
        for prod in df[biz_mask]['product_category'].tolist():
            issues.append(f'REMOVED_BUSINESS_ENTITY: {prod}')
    df = df[~biz_mask]

    # ── FIX 3: Remove subcategory = product_category entries ────
    redundant_mask = df.apply(is_redundant_entry, axis=1)
    redundant_count = redundant_mask.sum()
    if redundant_count:
        logger.info(f'Fix 3: Removing {redundant_count} redundant subcategory=product entries')
        for _, row in df[redundant_mask].iterrows():
            issues.append(f'REMOVED_REDUNDANT: {row["category"]} > {row["subcategory"]} > {row["product_category"]}')
    df = df[~redundant_mask]

    # ── FIX 5: Split Apparel Management Software subcategory ────
    ams_mask = df['subcategory'] == 'Apparel Management Software'
    ams_count = ams_mask.sum()
    if ams_count:
        logger.info(f'Fix 5: Splitting {ams_count} Apparel Management Software products into 6 subcategories')
        df.loc[ams_mask, 'subcategory'] = df.loc[ams_mask, 'product_category'].apply(get_ams_subcategory)

    # ── FIX 6: Move energy products to Energy & Power ───────────
    energy_mask = df['product_category'].apply(is_energy_product)
    energy_cats_to_move = df[energy_mask & (df['category'] != 'Electrical & Electronics')].index
    energy_elec = df[energy_mask & (df['category'] == 'Electrical & Electronics')].index

    # Solar panels, EV charging stay in Electrical & Electronics — only pure energy goes to new category
    pure_energy_mask = df['product_category'].apply(
        lambda x: any(kw in x.lower() for kw in [
            'solar energy monitoring', 'wind turbine', 'wind energy', 'wind power',
            'biomass energy', 'hydropower', 'tidal energy', 'geothermal energy',
            'fuel cell', 'hydrogen energy', 'biogas plant', 'power plant equipment',
            'renewable energy system', 'offshore wind',
        ])
    )
    energy_move_count = pure_energy_mask.sum()
    if energy_move_count:
        logger.info(f'Fix 6: Moving {energy_move_count} products to Energy & Power category')
        df.loc[pure_energy_mask, 'category'] = 'Energy & Power'
        df.loc[pure_energy_mask, 'subcategory'] = df.loc[pure_energy_mask, 'product_category'].apply(get_energy_subcategory)

    # ── FIX 7: Separate Food & Beverage from Agriculture ────────
    agri_mask = df['category'] == 'Agriculture & Food Products'
    df.loc[agri_mask, 'category'] = df.loc[agri_mask].apply(
        lambda row: get_food_vs_agri_category(row['subcategory'], row['product_category']),
        axis=1
    )
    food_bev_count = (df['category'] == 'Food & Beverage').sum()
    agri_count = (df['category'] == 'Agriculture & Farming').sum()
    agri_food_remaining = (df['category'] == 'Agriculture & Food Products').sum()
    logger.info(f'Fix 7: Food & Beverage={food_bev_count} | Agriculture & Farming={agri_count} | Remaining={agri_food_remaining}')

    # ── FIX 8: Add specification metadata column ─────────────────
    df['attributes'] = ''
    # Mark products that have specifications in their name
    spec_patterns = {
        r'\b\d+\s*(mm|cm|m|kg|ton|litre|l|ml|kw|hp|v|amp|mhz|ghz|inch|ft)\b': 'has_dimension',
        r'\b(grade [a-z]|grade-[a-z]|grade \d)\b': 'has_grade',
        r'\b(premium|standard|industrial|commercial|heavy[ -]duty|light[ -]duty)\b': 'has_quality_tier',
        r'\b(organic|natural|synthetic|chemical|bio|eco)\b': 'has_material_type',
    }
    for pattern, attr_val in spec_patterns.items():
        mask = df['product_category'].str.lower().str.contains(pattern, regex=True, na=False)
        df.loc[mask & (df['attributes'] == ''), 'attributes'] = attr_val
        df.loc[mask & (df['attributes'] != '') & (~df['attributes'].str.contains(attr_val, na=False)), 'attributes'] += f',{attr_val}'

    logger.info(f'Fix 8: Attribute metadata added. Products with specs: {(df["attributes"] != "").sum()}')

    # ── STANDARD DEDUPLICATION ───────────────────────────────────
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
    df = df.drop_duplicates(subset=['product_category'], keep='first')
    logger.info(f'Cross-category duplicates resolved: {before - len(df)}')

    # ── SOFTWARE MISPLACEMENT ────────────────────────────────────
    misplaced_mask = df.apply(
        lambda row: row['category'] in NON_SOFTWARE_CATEGORIES and is_software(str(row['product_category'])),
        axis=1
    )
    if misplaced_mask.sum():
        logger.warning(f'Misplaced software products auto-corrected: {misplaced_mask.sum()}')
        df.loc[misplaced_mask, 'category'] = 'Software & IT Solutions'

    # ── CASE DUPLICATE PRODUCT NAMES ────────────────────────────
    df['_lower'] = df['product_category'].str.lower().str.strip()
    df = df.drop_duplicates(subset=['_lower'], keep='first')
    df = df.drop(columns=['_lower'])

    # ── DROP EMPTY ───────────────────────────────────────────────
    df = df.dropna(subset=['category', 'subcategory', 'product_category'])
    df = df[df['product_category'].str.strip() != '']

    # ── SORT ─────────────────────────────────────────────────────
    df = df.sort_values(['category', 'subcategory', 'product_category']).reset_index(drop=True)

    final = len(df)
    sub_count = df['subcategory'].nunique()
    cat_count = df['category'].nunique()

    set_metric('final_products', final)
    set_metric('final_subcategories', sub_count)
    set_metric('final_categories', cat_count)
    set_metric('validation_issues', len(issues))
    set_metric('truncated_removed', truncated_count)
    set_metric('generic_removed', generic_count)
    set_metric('business_entities_removed', biz_count)
    set_metric('redundant_removed', redundant_count)
    set_metric('energy_products', (df['category'] == 'Energy & Power').sum())
    set_metric('food_beverage_products', (df['category'] == 'Food & Beverage').sum())
    set_metric('agriculture_products', (df['category'] == 'Agriculture & Farming').sum())

    output_path = os.path.join(PHASE5_OUTPUT_DIR, 'final_taxonomy.csv')
    df.to_csv(output_path, index=False, encoding='utf-8')
    logger.info(f'Final taxonomy: {output_path} ({final} rows, {sub_count} subcategories, {cat_count} categories)')
    logger.info(f'\nCategory distribution:\n{df["category"].value_counts().to_string()}')

    if issues:
        issues_path = os.path.join(PHASE5_OUTPUT_DIR, 'validation_issues.txt')
        with open(issues_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(issues))
        logger.info(f'Issues log: {issues_path} ({len(issues)} entries)')

    save_metrics()
    mark_completed('phase5')
    logger.info('Phase 5 complete.')

if __name__ == '__main__':
    run()
