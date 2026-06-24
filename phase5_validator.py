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
# FOOD & BEVERAGE vs AGRICULTURE & FARMING SUBCATEGORY SPLIT
# Applied AFTER Phase 4 synonym merge to re-establish separation
# ============================================================
FOOD_BEVERAGE_SUBCATEGORIES = {
    'Bakery & Confectionery Products',
    'Beverages (Tea, Coffee, Juices)',
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
    'Tobacco & Smoking Products',
    'Fresh Fruits & Vegetables',
    'Spices & Herbs',
    'Grains, Cereals & Pulses',
    'Baking Ingredients',
}

AGRICULTURE_FARMING_SUBCATEGORIES = {
    'Seeds & Planting Materials',
    'Fertilizers & Soil Conditioners',
    'Pesticides & Crop Protection',
    'Agricultural Equipment & Implements',
    'Agricultural Produce',
    'Organic Produce',
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
    'Animal Feed & Nutrition',
}

# ============================================================
# FIX A — Redistribute Agriculture & Food Products leftover
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
    'Sports Nutrition & Supplements': ('Health & Personal Care', 'Health Supplements & Nutraceuticals'),
    'Tobacco & Smoking Products': ('Food & Beverage', 'Tobacco & Smoking Products'),
    'Training & Capacity Building': ('Services & Support', 'Training & Skill Development'),
}

# ============================================================
# FIX B — Remove Energy & Power (too few products)
# ============================================================
FIX_B_ENERGY_REMAP = {
    'Biogas Plant Machinery': ('Machinery & Equipment', 'Renewable Energy Machinery'),
    'Solar Energy Monitoring Systems': ('Software & IT Solutions', 'IoT & Smart Building Software'),
    'Wind Turbine Commissioning': ('Services & Support', 'Engineering & Technical Services'),
}

# ============================================================
# FIX C — Reclassify ERP overload
# ============================================================
FIX_C_PRODUCT_SUBCATEGORY = {
    # Creative & Game Development Software
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
    # IoT & Smart Building Software
    'Air Quality Monitoring Devices': 'IoT & Smart Building Software',
    'App-Based Monitoring Systems': 'IoT & Smart Building Software',
    'Automated Alert & Reporting Tools': 'IoT & Smart Building Software',
    'Battery Management Systems (BMS)': 'IoT & Smart Building Software',
    'Building Management System (BMS) Panels': 'IoT & Smart Building Software',
    'CO2 & Air Quality Sensors': 'IoT & Smart Building Software',
    'Cloud-Based Smart Building Platforms': 'IoT & Smart Building Software',
    'Cold Chain Temperature Monitoring Systems': 'IoT & Smart Building Software',
    'Data Loggers for Greenhouses': 'IoT & Smart Building Software',
    'Home & Building Voice Assistants Integration': 'IoT & Smart Building Software',
    'Integrated Facility Dashboards': 'IoT & Smart Building Software',
    'IoT Gateways & Controllers': 'IoT & Smart Building Software',
    'IoT Solutions For Smart Farming': 'IoT & Smart Building Software',
    'IoT-Based Cold Chain Management': 'IoT & Smart Building Software',
    'IoT-Enabled Smart Controllers': 'IoT & Smart Building Software',
    'Leak Detection & Alert Devices': 'IoT & Smart Building Software',
    'Motorized Curtain & Blind Controls': 'IoT & Smart Building Software',
    'Occupancy Sensors & Timers': 'IoT & Smart Building Software',
    'Power Factor Correction Devices': 'IoT & Smart Building Software',
    'Remote Lock/Unlock Access Systems': 'IoT & Smart Building Software',
    'SCADA Software Licenses': 'IoT & Smart Building Software',
    'SCADA for Compressors': 'IoT & Smart Building Software',
    'Smart Building Mobile Apps': 'IoT & Smart Building Software',
    'Smart CCTV Monitoring Systems': 'IoT & Smart Building Software',
    'Smart Grid Controllers': 'IoT & Smart Building Software',
    'Smart Lighting Control Systems': 'IoT & Smart Building Software',
    'Smart Meters (Water, Electricity, Gas)': 'IoT & Smart Building Software',
    'Smart Video Door Phones': 'IoT & Smart Building Software',
    'Smart Yoga Devices & Apps': 'IoT & Smart Building Software',
    'Survey Software & Data Loggers': 'IoT & Smart Building Software',
    'Wi-Fi & Bluetooth Smart Controllers': 'IoT & Smart Building Software',
    'Wireless Control Systems': 'IoT & Smart Building Software',
    'Zigbee/Z-Wave Enabled Devices': 'IoT & Smart Building Software',
    'HVAC Automation Controls': 'IoT & Smart Building Software',
    # CRM & Sales Automation
    'CRM & Sales Automation Tools': 'CRM & Sales Automation Software',
    'Cloud-Based Fashion POS Software': 'CRM & Sales Automation Software',
    'Cloud-Based Apparel ERP Providers': 'CRM & Sales Automation Software',
    'Customer Relationship Management (CRM) Software': 'CRM & Sales Automation Software',
    'Crm Software Development': 'CRM & Sales Automation Software',
    'Custom Fashion POS Setup': 'CRM & Sales Automation Software',
    'Email Marketing & Automation Tools': 'CRM & Sales Automation Software',
    'Email Marketing Software (Mailchimp, Sendinblue)': 'CRM & Sales Automation Software',
    'Helpdesk & Support Ticketing Systems': 'CRM & Sales Automation Software',
    'Loyalty Program Integrated POS': 'CRM & Sales Automation Software',
    'Marketplace Order Sync Tools (Amazon, Flipkart)': 'CRM & Sales Automation Software',
    'Mobile POS Apps for Fashion Stores': 'CRM & Sales Automation Software',
    'POS Integration for Fashion Retail': 'CRM & Sales Automation Software',
    'POS with WhatsApp Invoice Integration': 'CRM & Sales Automation Software',
    'Point of Sale (POS) Systems': 'CRM & Sales Automation Software',
    'Return & Exchange Management Systems': 'CRM & Sales Automation Software',
    'SaaS Subscription POS Providers': 'CRM & Sales Automation Software',
    'Sales Analytics & Reporting Tools': 'CRM & Sales Automation Software',
    # HR & Payroll
    'Attendance & HRMS Software': 'HR & Payroll Software',
    'Biometric Attendance Systems': 'HR & Payroll Software',
    'HR & Payroll Management Software': 'HR & Payroll Software',
    'HRMS & Payroll Integration Services': 'HR & Payroll Software',
    'Human Resource Management Systems (HRMS)': 'HR & Payroll Software',
    'Payroll Software Solutions': 'HR & Payroll Software',
    'Time & Attendance Management Software': 'HR & Payroll Software',
    # Healthcare IT
    'Cloud-Based Medical Transcription Tools': 'Healthcare IT Software',
    'Diagnostic Software & Scanners': 'Healthcare IT Software',
    'Go-To-Market Strategy for Wellness Brands': 'Healthcare IT Software',
    'Healthcare Startup Business Strategy': 'Healthcare IT Software',
    'Hospital Information Management Systems (HIMS)': 'Healthcare IT Software',
    'Medical Billing Software Solutions': 'Healthcare IT Software',
    'Medical VR Equipment': 'Healthcare IT Software',
    # Industry-Specific
    '3D Virtual Prototyping': 'Industry-Specific Software',
    'AI-Based Crop Advisory System Setup': 'Industry-Specific Software',
    'AI-Based Surveillance Cleaning Bots': 'Industry-Specific Software',
    'AI-Driven Inventory Optimization Tools': 'Industry-Specific Software',
    'AI-based Predictive Maintenance Tools': 'Industry-Specific Software',
    'Adulteration Detection (Milk, Oils, Spices)': 'Industry-Specific Software',
    'Agri ERP Software Implementation': 'Industry-Specific Software',
    'Allergen Testing (Gluten, Soy, Nuts)': 'Industry-Specific Software',
    'Automated Optical Inspection (AOI)': 'Industry-Specific Software',
    'CNC Cutting Software & Controllers': 'Industry-Specific Software',
    'CAD & 3D Design Software (AutoCAD, SolidWorks)': 'Industry-Specific Software',
    'Chemical Process Control Panels': 'Industry-Specific Software',
    'Crop Protection Monitoring Systems': 'Industry-Specific Software',
    'Custom Color Development (Eco-Friendly)': 'Industry-Specific Software',
    'Dealership Management Software': 'Industry-Specific Software',
    'Design Software (Adobe CC, CorelDRAW)': 'Industry-Specific Software',
    'Digital Vehicle Inspection Software': 'Industry-Specific Software',
    'Export Certification Services (USFDA, EU Standards)': 'Industry-Specific Software',
    'Export Documentation & Compliance Software': 'Industry-Specific Software',
    'FSSAI Compliance Assistance': 'Industry-Specific Software',
    'Face Recognition Access Systems': 'Industry-Specific Software',
    'Farm Automation Planning': 'Industry-Specific Software',
    'HMI Control Panels': 'Industry-Specific Software',
    'Halal, Kosher Testing & Documentation': 'Industry-Specific Software',
    'Heavy Metal Analysis (Lead, Arsenic, Mercury)': 'Industry-Specific Software',
    'ISO 22000, HACCP, GMP Certification Support': 'Industry-Specific Software',
    'Label Claim Validation Services': 'Industry-Specific Software',
    'Label Design Software': 'Industry-Specific Software',
    'Microbiological Testing (Bacteria, Pathogens)': 'Industry-Specific Software',
    'Nutritional Analysis (Calories, Proteins, Vitamins)': 'Industry-Specific Software',
    'Organic Certification Testing': 'Industry-Specific Software',
    'PLC Integrated Mixing Systems': 'Industry-Specific Software',
    'Programming Cables & Software': 'Industry-Specific Software',
    'Sampling & Small Batch Eco Dye Services': 'Industry-Specific Software',
    'Shelf Life & Stability Testing': 'Industry-Specific Software',
    'Tech Pack to Sample Conversion': 'Industry-Specific Software',
    'Training Materials For Waste Handlers': 'Industry-Specific Software',
    'UX/UI Design For Infotainment Systems': 'Industry-Specific Software',
    'Vibration Monitoring for Bearings': 'Industry-Specific Software',
    'Waste Tracking Logs & Registers': 'Industry-Specific Software',
    'Water Quality Testing for Food Units': 'Industry-Specific Software',
    # Cloud & Productivity
    'Accounting & Billing Software Development': 'Cloud & Productivity Software',
    'Accounting & Bookkeeping SaaS': 'Cloud & Productivity Software',
    'Accounting Software (Tally, QuickBooks, Zoho Books)': 'Cloud & Productivity Software',
    'Agile & Scrum Project Management': 'Cloud & Productivity Software',
    'Api Development & Integration': 'Cloud & Productivity Software',
    'Audit & Documentation Solutions': 'Cloud & Productivity Software',
    'Audit Trail Reports & Record Logs': 'Cloud & Productivity Software',
    'Automated Billing & Invoicing Systems': 'Cloud & Productivity Software',
    'Cloud Storage & File Sharing Services': 'Cloud & Productivity Software',
    'Cloud Storage Subscriptions': 'Cloud & Productivity Software',
    'Compliance Checklists & SOP Posters': 'Cloud & Productivity Software',
    'Desktop Application Development': 'Cloud & Productivity Software',
    'Developer Tools (IDE, GitHub, JetBrains)': 'Cloud & Productivity Software',
    'Document Management & E-signature Tools': 'Cloud & Productivity Software',
    'Electronic Signature Software': 'Cloud & Productivity Software',
    'Encrypted File Transmission Systems': 'Cloud & Productivity Software',
    'Hybrid Event Solutions': 'Cloud & Productivity Software',
    'ID Card Design Software': 'Cloud & Productivity Software',
    'Laptop & Desktop Leasing': 'Cloud & Productivity Software',
    'Network & IT Tool Kits': 'Cloud & Productivity Software',
    'Office Productivity Software (MS Office, Google Workspace)': 'Cloud & Productivity Software',
    'Operating System Licenses (Windows, Linux)': 'Cloud & Productivity Software',
    'Post-Implementation Support & Upgrades': 'Cloud & Productivity Software',
    'Project Management & Collaboration Tools': 'Cloud & Productivity Software',
    'Project Management Software (Asana, Trello, Monday.com)': 'Cloud & Productivity Software',
    'Project Planning & Coordination Services': 'Cloud & Productivity Software',
    'SaaS Product Development': 'Cloud & Productivity Software',
    'Secure Document Sharing & Workflow Automation': 'Cloud & Productivity Software',
    'Serialization And Track And Trace Systems': 'Cloud & Productivity Software',
    'Smartwatch App Development Services': 'Cloud & Productivity Software',
    'Software Development Consulting': 'Cloud & Productivity Software',
    'Software Maintenance & Support': 'Cloud & Productivity Software',
    'Speech Recognition AI Tools': 'Cloud & Productivity Software',
    'Sustainability & Compliance Reporting': 'Cloud & Productivity Software',
    'Task Management & Reminder Services': 'Cloud & Productivity Software',
    'Video Conferencing Software (Zoom, Teams, Webex)': 'Cloud & Productivity Software',
    'Virtual Classrooms & Meeting Rooms': 'Cloud & Productivity Software',
    'Virtual Event Management': 'Cloud & Productivity Software',
    'Virtual Group Classes': 'Cloud & Productivity Software',
    'Voice Recognition Toys': 'Cloud & Productivity Software',
    'Web Application Development': 'Cloud & Productivity Software',
    'Website & Landing Page Builders': 'Cloud & Productivity Software',
    'Workflow Automation Software': 'Cloud & Productivity Software',
}

FIX_C_PRODUCT_CATEGORY_DEST = {
    'Augmented Reality (AR) Toys': ('Home & Lifestyle', "Children's Play Equipment & Toys"),
    'Baby Monitors': ('Home & Lifestyle', "Children's Play Equipment & Toys"),
    'Digital Flashcards': ('Home & Lifestyle', "Children's Play Equipment & Toys"),
    'Electronic Board Games': ('Home & Lifestyle', "Children's Play Equipment & Toys"),
    'Electronic Building Blocks': ('Home & Lifestyle', "Children's Play Equipment & Toys"),
    'Electronic Drawing Pads': ('Home & Lifestyle', "Children's Play Equipment & Toys"),
    "Kids' Tablets & Learning Pads": ('Home & Lifestyle', "Children's Play Equipment & Toys"),
    'Language Learning Devices': ('Home & Lifestyle', "Children's Play Equipment & Toys"),
    'Musical Toys': ('Home & Lifestyle', "Children's Play Equipment & Toys"),
    'Remote-Controlled Educational Bots': ('Home & Lifestyle', "Children's Play Equipment & Toys"),
    'Sound and Light Toys': ('Home & Lifestyle', "Children's Play Equipment & Toys"),
    'Box Build Assembly': ('Electrical & Electronics', 'PCB & Electronic Components'),
    'Conformal Coating Services': ('Electrical & Electronics', 'PCB & Electronic Components'),
    'Custom Electronic Assembly Services': ('Electrical & Electronics', 'PCB & Electronic Components'),
    'High Volume PCB Assembly': ('Electrical & Electronics', 'PCB & Electronic Components'),
    'Mixed Technology Assembly': ('Electrical & Electronics', 'PCB & Electronic Components'),
    'PCB Soldering Services': ('Electrical & Electronics', 'PCB & Electronic Components'),
    'PCBA Testing & Quality Control': ('Electrical & Electronics', 'PCB & Electronic Components'),
    'Prototype PCB Assembly': ('Electrical & Electronics', 'PCB & Electronic Components'),
    'Reflow Soldering Services': ('Electrical & Electronics', 'PCB & Electronic Components'),
    'Surface Mount Technology (SMT) Assembly': ('Electrical & Electronics', 'PCB & Electronic Components'),
    'Through-Hole Assembly Services': ('Electrical & Electronics', 'PCB & Electronic Components'),
    'Turnkey PCB Assembly Services': ('Electrical & Electronics', 'PCB & Electronic Components'),
    'Wave Soldering Services': ('Electrical & Electronics', 'PCB & Electronic Components'),
    'X-Ray Inspection For PCBAs': ('Electrical & Electronics', 'PCB & Electronic Components'),
    'Barcode Labels For Waste Bags': ('Packaging & Printing', 'Barcode Labels & RFID Tags'),
    'Barcode & RFID Tagging Systems': ('Packaging & Printing', 'Barcode Labels & RFID Tags'),
    'Ink Supplies': ('Packaging & Printing', 'Printing Consumables & Inks'),
    'Lighting Design Consultants': ('Services & Support', 'Engineering & Technical Services'),
    'Operator Training Programs': ('Services & Support', 'Training & Skill Development'),
}

# ============================================================
# FIX D — Rename invalid software subcategories
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
# FIX E — Sports construction to correct categories
# ============================================================
FIX_E_SPORTS_CONSTRUCTION = {
    'Badminton Court Construction': ('Construction & Infrastructure', 'Sports & Recreational Infrastructure'),
    'Basketball Court Construction': ('Construction & Infrastructure', 'Sports & Recreational Infrastructure'),
    'Cricket Ground Development': ('Construction & Infrastructure', 'Sports & Recreational Infrastructure'),
    'Football Field Construction': ('Construction & Infrastructure', 'Sports & Recreational Infrastructure'),
    'Indoor Sports Hall Construction': ('Construction & Infrastructure', 'Sports & Recreational Infrastructure'),
    'Multi-Sport Arena Construction': ('Construction & Infrastructure', 'Sports & Recreational Infrastructure'),
    'Scoreboard And Display Installation': ('Electrical & Electronics', 'Surveillance & Security Systems'),
    'Sports Flooring Installation (Pvc, Wooden, Pu)': ('Construction & Infrastructure', 'Tiles, Marble, Granite & Flooring'),
    'Sports Lighting Systems': ('Electrical & Electronics', 'Lighting Fixtures & Fittings'),
    'Stadium Seating Installation': ('Construction & Infrastructure', 'Sports & Recreational Infrastructure'),
    'Swimming Pool Construction': ('Construction & Infrastructure', 'Sports & Recreational Infrastructure'),
    'Tennis Court Construction': ('Construction & Infrastructure', 'Sports & Recreational Infrastructure'),
    'Gym And Fitness Center Setup': ('Services & Support', 'Engineering & Technical Services'),
}

NON_SOFTWARE_CATEGORIES = {
    'Apparel & Fashion', 'Agriculture & Food Products', 'Agriculture & Farming',
    'Food & Beverage', 'Machinery & Equipment', 'Chemicals & Raw Materials',
    'Electrical & Electronics', 'Construction & Infrastructure',
    'Health & Personal Care', 'Automotive & Transport', 'Home & Lifestyle',
    'Tools & Hardware', 'Packaging & Printing', 'Office Supplies & Equipment',
    'Sports & Entertainment',
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
    'smart thermometer', 'alarm system', 'grout filling',
    'sealant application', 'organic dye', 'home lift',
    'automation system installation', 'fleet tracking',
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

    logger.info('Starting Phase 5 — Validator v5 (Final)')

    input_path = os.path.join(PHASE4_OUTPUT_DIR, 'normalized.csv')
    if not os.path.exists(input_path):
        raise FileNotFoundError(f'Phase 4 output not found: {input_path}')

    df = pd.read_csv(input_path)
    if 'attributes' in df.columns:
        df = df.drop(columns=['attributes'])

    initial = len(df)
    logger.info(f'Input rows: {initial}')

    # ── FIX A ───────────────────────────────────────────────────
    afp_mask = df['category'] == 'Agriculture & Food Products'
    logger.info(f'Fix A: Processing {afp_mask.sum()} Agriculture & Food Products rows')
    rows_to_delete = []
    for idx, row in df[afp_mask].iterrows():
        sub = row['subcategory']
        dest = FIX_A_REMAP.get(sub)
        if dest is None:
            rows_to_delete.append(idx)
        else:
            df.at[idx, 'category'] = dest[0]
            df.at[idx, 'subcategory'] = dest[1]
    if rows_to_delete:
        df = df.drop(index=rows_to_delete)
    logger.info(f'Fix A: Done. Deleted {len(rows_to_delete)} Excess Inventory rows')

    # ── FIX B ───────────────────────────────────────────────────
    energy_mask = df['category'] == 'Energy & Power'
    logger.info(f'Fix B: Remapping {energy_mask.sum()} Energy & Power products')
    for idx, row in df[energy_mask].iterrows():
        prod = row['product_category']
        new_cat, new_sub = FIX_B_ENERGY_REMAP.get(
            prod, ('Electrical & Electronics', 'Renewable Energy Equipment'))
        df.at[idx, 'category'] = new_cat
        df.at[idx, 'subcategory'] = new_sub
    logger.info('Fix B: Energy & Power eliminated')

    # ── FIX C ───────────────────────────────────────────────────
    erp_mask = (
        (df['category'] == 'Software & IT Solutions') &
        (df['subcategory'] == 'ERP & Business Management Software')
    )
    logger.info(f'Fix C: Reclassifying {erp_mask.sum()} ERP overload products')
    for idx, row in df[erp_mask].iterrows():
        prod = row['product_category']
        if prod in FIX_C_PRODUCT_SUBCATEGORY:
            new_sub = FIX_C_PRODUCT_SUBCATEGORY[prod]
            if new_sub is None and prod in FIX_C_PRODUCT_CATEGORY_DEST:
                new_cat, new_sub2 = FIX_C_PRODUCT_CATEGORY_DEST[prod]
                df.at[idx, 'category'] = new_cat
                df.at[idx, 'subcategory'] = new_sub2
            elif new_sub:
                df.at[idx, 'subcategory'] = new_sub
    logger.info('Fix C: Done')

    # ── FIX D ───────────────────────────────────────────────────
    sw_mask = df['category'] == 'Software & IT Solutions'
    for idx, row in df[sw_mask].iterrows():
        if row['subcategory'] in FIX_D_SUBCATEGORY_RENAME:
            df.at[idx, 'subcategory'] = FIX_D_SUBCATEGORY_RENAME[row['subcategory']]
    logger.info('Fix D: Invalid software subcategories renamed')

    # ── FIX E ───────────────────────────────────────────────────
    sports_eng_mask = (
        (df['category'] == 'Sports & Entertainment') &
        (df['subcategory'] == 'Engineering & Technical Services')
    )
    logger.info(f'Fix E: Moving {sports_eng_mask.sum()} sports construction products')
    for idx, row in df[sports_eng_mask].iterrows():
        prod = row['product_category']
        new_cat, new_sub = FIX_E_SPORTS_CONSTRUCTION.get(
            prod, ('Construction & Infrastructure', 'Sports & Recreational Infrastructure'))
        df.at[idx, 'category'] = new_cat
        df.at[idx, 'subcategory'] = new_sub
    logger.info('Fix E: Done')

    # ── FOOD & BEVERAGE RE-SPLIT (after Phase 4 merge) ──────────
    # Phase 4 synonym merge collapsed Food & Beverage back into Agriculture & Farming
    # Re-establish the split based on subcategory names
    agri_mask = df['category'].isin(['Agriculture & Farming', 'Agriculture & Food Products'])
    food_sub_mask = df['subcategory'].isin(FOOD_BEVERAGE_SUBCATEGORIES)
    food_reclassify_mask = agri_mask & food_sub_mask
    food_reclassify_count = food_reclassify_mask.sum()
    if food_reclassify_count:
        logger.info(f'Food/Agri split: Moving {food_reclassify_count} products to Food & Beverage')
        df.loc[food_reclassify_mask, 'category'] = 'Food & Beverage'

    agri_sub_mask = df['subcategory'].isin(AGRICULTURE_FARMING_SUBCATEGORIES)
    agri_reclassify_mask = (df['category'] == 'Food & Beverage') & agri_sub_mask
    agri_reclassify_count = agri_reclassify_mask.sum()
    if agri_reclassify_count:
        logger.info(f'Food/Agri split: Moving {agri_reclassify_count} products to Agriculture & Farming')
        df.loc[agri_reclassify_mask, 'category'] = 'Agriculture & Farming'

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

    # ── DROP EMPTY ───────────────────────────────────────────────
    df = df.dropna(subset=['category', 'subcategory', 'product_category'])
    df = df[df['product_category'].str.strip() != '']

    # ── SORT ─────────────────────────────────────────────────────
    df = df.sort_values(['category', 'subcategory', 'product_category']).reset_index(drop=True)

    final = len(df)
    cat_count = df['category'].nunique()
    sub_count = df['subcategory'].nunique()

    # ── VALIDATION REPORT ────────────────────────────────────────
    afp_remaining = len(df[df['category'] == 'Agriculture & Food Products'])
    energy_remaining = len(df[df['category'] == 'Energy & Power'])
    erp_remaining = len(df[
        (df['category'] == 'Software & IT Solutions') &
        (df['subcategory'] == 'ERP & Business Management Software')
    ])
    sports_eng_remaining = len(df[
        (df['category'] == 'Sports & Entertainment') &
        (df['subcategory'] == 'Engineering & Technical Services')
    ])
    food_bev_count = len(df[df['category'] == 'Food & Beverage'])
    agri_count = len(df[df['category'] == 'Agriculture & Farming'])

    logger.info(f'\n{"="*55}')
    logger.info(f'VALIDATION RESULTS:')
    logger.info(f'  Fix A — Agriculture & Food Products leftover: {afp_remaining} (target: 0)')
    logger.info(f'  Fix B — Energy & Power remaining: {energy_remaining} (target: 0)')
    logger.info(f'  Fix C — ERP overload remaining: {erp_remaining} (target: <50)')
    logger.info(f'  Fix E — Sports Eng & Technical: {sports_eng_remaining} (target: 0)')
    logger.info(f'  Food & Beverage: {food_bev_count} products')
    logger.info(f'  Agriculture & Farming: {agri_count} products')
    logger.info(f'{"="*55}')

    sw_subs = df[df['category'] == 'Software & IT Solutions']['subcategory'].value_counts()
    logger.info(f'\nSoftware & IT Solutions:\n{sw_subs.to_string()}')
    logger.info(f'\nCategory distribution:\n{df["category"].value_counts().to_string()}')

    set_metric('final_products', final)
    set_metric('final_subcategories', sub_count)
    set_metric('final_categories', cat_count)
    set_metric('food_beverage_products', food_bev_count)
    set_metric('agriculture_farming_products', agri_count)
    set_metric('fix_a_remaining', afp_remaining)
    set_metric('fix_b_remaining', energy_remaining)
    set_metric('fix_c_erp_remaining', erp_remaining)
    set_metric('fix_e_remaining', sports_eng_remaining)

    output_path = os.path.join(PHASE5_OUTPUT_DIR, 'final_taxonomy.csv')
    df.to_csv(output_path, index=False, encoding='utf-8')
    logger.info(f'Output: {output_path} ({final} rows | {sub_count} subcategories | {cat_count} categories)')

    save_metrics()
    mark_completed('phase5')
    logger.info('Phase 5 complete.')

if __name__ == '__main__':
    run()
