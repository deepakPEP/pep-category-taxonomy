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
    'avocado oil', 'camelina oil',
    'frozen food', 'frozen meal', 'frozen vegetable', 'frozen fruit',
    'frozen chicken', 'frozen fish', 'frozen prawn', 'frozen biryani',
    'frozen breakfast', 'frozen indian', 'frozen curry',
    'instant food', 'ready to eat', 'ready-to-eat', 'rte food',
    'canned food', 'preserved food', 'canned ready meal',
    'diabetic-friendly instant',
    'chicken cut', 'fresh chicken', 'mutton', 'lamb cut', 'fresh fish',
    'prawn', 'shrimp', 'seafood', 'tuna', 'salmon', 'broiler chicken',
    'boneless meat', 'horeca pack',
    'cigarette', 'cigar', 'tobacco product',
    'baby food', 'infant formula', 'baby cereal', 'baby puree',
    'electrolyte mix for infant', 'prebiotic', 'probiotic powder',
    'protein powder', 'mass gainer', 'pre-workout supplement',
    'bcaa supplement', 'creatine supplement', 'sports drink',
    'electrolyte drink for athlete',
    'basmati rice', 'white rice', 'brown rice', 'rice variety',
    'wheat flour', 'atta', 'maida', 'besan', 'flour variety',
    'dal variety', 'lentil variety', 'pulse variety', 'chana',
    'rajma', 'moong', 'toor dal', 'urad dal',
    'turmeric', 'black pepper', 'cumin', 'coriander', 'cardamom',
    'cinnamon', 'clove', 'ginger powder', 'chilli powder',
    'masala', 'spice blend', 'kokum', 'vitamin-infused water',
    'chewing gum', 'bubble gum', 'danish', 'donut', 'eclair',
    'family pack snack', 'khara boondi', 'mixture snack',
    'bulk can', 'cooking oil bulk',
]

FOOD_SUBCATEGORY_MAP = [
    (['tea', 'coffee', 'beverage', 'drink', 'lassi', 'buttermilk',
      'coconut water', 'energy drink', 'smoothie', 'shake',
      'kokum', 'vitamin-infused water'], 'Beverages (Tea, Coffee, Juices)'),
    (['milk', 'paneer', 'ghee', 'butter', 'cheese', 'curd', 'yogurt',
      'cream', 'dairy', 'whey protein'], 'Dairy Products & Alternatives'),
    (['bread', 'cake', 'biscuit', 'cookie', 'chocolate', 'candy', 'sweet',
      'mithai', 'laddoo', 'barfi', 'halwa', 'gulab jamun', 'rasgulla',
      'confectionery', 'pastry', 'muffin', 'cupcake', 'bakery', 'toffee',
      'chewing gum', 'bubble gum', 'danish', 'donut', 'eclair'], 'Bakery & Confectionery Products'),
    (['snack', 'namkeen', 'bhujia', 'chiwda', 'popcorn', 'chips',
      'farsan', 'gathiya', 'makhana', 'peanut snack',
      'family pack snack', 'khara boondi', 'mixture snack'], 'Snacks & Namkeens'),
    (['pickle', 'ketchup', 'chutney', 'jam', 'sauce', 'paste',
      'mayonnaise', 'vinegar', 'mustard', 'dressing', 'achar'], 'Condiments & Sauces'),
    (['edible oil', 'cooking oil', 'sunflower oil', 'mustard oil',
      'coconut oil', 'groundnut oil', 'olive oil', 'sesame oil',
      'rice bran oil', 'soybean oil', 'palm oil', 'canola oil',
      'avocado oil', 'camelina oil', 'bulk can'], 'Edible Oils & Fats'),
    (['frozen food', 'frozen meal', 'frozen vegetable', 'frozen fruit',
      'frozen chicken', 'frozen fish', 'frozen prawn', 'frozen biryani',
      'frozen breakfast', 'frozen indian', 'frozen curry'], 'Frozen & Processed Foods'),
    (['instant food', 'ready to eat', 'ready-to-eat', 'rte food',
      'canned food', 'preserved food', 'canned ready meal',
      'diabetic-friendly instant'], 'Ready-to-Eat & Instant Foods'),
    (['chicken cut', 'fresh chicken', 'mutton', 'lamb cut', 'fresh fish',
      'prawn', 'shrimp', 'seafood', 'tuna', 'salmon', 'broiler chicken',
      'boneless meat', 'horeca pack'], 'Meat, Poultry & Seafood'),
    (['cigarette', 'cigar', 'tobacco product'], 'Tobacco & Smoking Products'),
    (['baby food', 'infant formula', 'baby cereal', 'baby puree',
      'electrolyte mix for infant', 'prebiotic', 'probiotic powder',
      'export-ready baby nutrition'], 'Baby Food Products'),
    (['protein powder', 'mass gainer', 'pre-workout supplement',
      'bcaa supplement', 'creatine supplement', 'sports drink',
      'electrolyte drink for athlete'], 'Sports Nutrition Products'),
]

# Food subcategories that should be in Food & Beverage not Agriculture
FOOD_SUBCATEGORIES_IN_AGRI = {
    'Baby Food Products', 'Bakery & Confectionery Products',
    'Beverages (Tea, Coffee, Juices)', 'Edible Oils & Fats',
    'Frozen & Processed Foods', 'Meat, Poultry & Seafood',
    'Ready-to-Eat & Instant Foods', 'Snacks & Namkeens',
    'Condiments & Sauces', 'Dairy Products & Alternatives',
    'Tobacco & Smoking Products', 'Sports Nutrition Products',
}

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
# GARMENT MANUFACTURING (OEM/ODM) REMAP
# Map each product to correct Apparel subcategory
# ============================================================
GARMENT_OEM_REMAP = {
    'Infant & Toddler Apparel ODM': 'Kids & Baby Wear',
    'Jeans & Bottoms Manufacturers': 'Men\'s Wear',
    'Kids\' Clothing OEM': 'Kids & Baby Wear',
    'Kids\' Ethnic Wear Producers': 'Kids & Baby Wear',
    'Men\'s Activewear Manufacturers': 'Sportswear & Athletic Apparel',
    'Men\'s Casual Wear OEM': 'Men\'s Wear',
    'Men\'s Ethnic Wear OEM': 'Ethnic & Cultural Clothing',
    'Men\'s Formal Wear ODM': 'Men\'s Wear',
    'Men\'s Innerwear & Undergarment OEM': 'Men\'s Wear',
    'Men\'s Outerwear Producers': 'Men\'s Wear',
    'School Uniform Manufacturers': 'Workwear & Safety Apparel',
    'Shirts & Blouses ODM': 'T-Shirts, Polos, Shirts',
    'T-Shirts & Polos OEM': 'T-Shirts, Polos, Shirts',
    'Women\'s Dresses & Gowns Manufacturers': 'Dresses, Gowns, Skirts',
    'Women\'s Ethnic Wear ODM': 'Sarees, Kurtis, Salwar Sets',
    'Women\'s Fashion Wear OEM': 'Women\'s Wear',
    'Women\'s Lingerie OEM': 'Women\'s Wear',
    'Women\'s Maternity Wear ODM': 'Women\'s Wear',
    'Women\'s Sportswear Manufacturers': 'Sportswear & Athletic Apparel',
}

# ============================================================
# INDUSTRY-SPECIFIC SOFTWARE RECLASSIFICATION
# ============================================================
ISS_HEALTHCARE = {
    'AI Symptom Checker Integrations', 'AI-Based Diagnosis Support Tools',
    'AI-Powered Image Diagnostics', 'API Integration Tools for Clinics',
    'Automated Lab Result Reporting', 'Billing, Invoicing & Insurance Claims Software',
    'Chatbots for Patient Queries', 'Clinic Management Software',
    'Clinical Decision Support Systems', 'Cloud-Based Data Storage for Medical Records',
    'Cloud-Based EHR Systems', 'Cloud-Based Medical Transcription Tools',
    'Customizable EMR Templates', 'DICOM Image Viewers',
    'Data Loggers for Medical Transport', 'Diagnostic Software & Scanners',
    'Digital Consent & EHR Forms', 'E-Prescription Tools',
    'EHR Mobile Applications', 'Electronic Data Capture (EDC) Services',
    'HIPAA & GDPR Compliance Tools', 'HIPAA-Compliant Communication Tools',
    'Healthcare CRM Tools', 'Hospital Information Management Systems (HIMS)',
    'Inventory Management for Labs & Pharmacies', 'Lab & Diagnostic Data Integration',
    'Laboratory Information Systems (LIS)', 'Livestock Health Record Software',
    'Medical Billing Software Solutions', 'Medical Data Backup & Recovery Solutions',
    'Medical NLP & Data Extraction Tools', 'Mobile Health Engagement Apps',
    'OPD & IPD Management Tools', 'Online Booking & Scheduling Systems',
    'PACS (Picture Archiving and Communication Systems)',
    'Patient Feedback & Survey Platforms', 'Patient Portal Integrations',
    'Patient Portals & Mobile Apps', 'Patient Registration & Queue Management Systems',
    'Population Health Management Software', 'Practice Management Systems Integration',
    'Predictive Health Analytics Tools', 'Radiology Information Systems (RIS)',
    'Remote Diagnosis Platforms', 'Remote Patient Monitoring Systems',
    'Secure Cloud Hosting for Medical Data', 'Sleep Coaching Apps & Programs',
    'Specialty-Specific Telehealth Solutions (Dermatology, Psychiatry)',
    'Teleconsultation Platforms', 'Telemedicine Software (General Practitioners)',
    'Video Consultation API Solutions', 'Virtual Waiting Room Software',
    'White-Label Telehealth Software', 'ePharmacy & Online Ordering Platforms',
    'AI-Based Diagnosis Support Tools', 'Automated Lab Result Reporting',
    'Ambulance Fleet Management Software',
}

ISS_IOT = {
    'Access Control & Audit Logs', 'Automated Alert & Reporting Tools',
    'Building Management System (BMS) Integration',
    'Building Management System (BMS) Panels',
    'Cloud-Based Cold Chain Monitoring Dashboards',
    'Cloud-Based Smart Building Platforms', 'Compressor Control Panels',
    'Custom Automation Software (SaaS)', 'Energy Monitoring Systems for Compressors',
    'Integrated Facility Dashboards', 'IoT-Based Asset Monitoring Platforms',
    'IoT-Based Cold Chain Management', 'IoT-Based Farm Management Systems',
    'IoT-Based Fleet Management Platforms', 'Office IoT Integration Tools',
    'Personal Alarm Systems', 'Real-Time GPS Trackers with Temperature Sensors',
    'SCADA Software Licenses', 'SCADA for Compressors',
    'Smart Building Mobile Apps', 'Workplace Safety Cameras',
}

ISS_CRM = {
    'CRM & Sales Automation Tools', 'CRM Software Development',
    'Email Marketing & Automation Tools',
    'Email Marketing Software (Mailchimp, Sendinblue)',
    'Helpdesk & Support Ticketing Systems',
    'Online Fitness Program Marketplaces', 'POS Integration for Fashion Retail',
    'Point of Sale (POS) Systems', 'Stock Replenishment & Forecasting Tools',
    'Buyer Order Tracking Portals',
}

ISS_HR = {
    'Attendance & HRMS Software', 'HR & Payroll Management Software',
    'HRMS & Payroll Integration Services',
    'Human Resource Management Systems (HRMS)',
    'Payroll Software Solutions', 'Time & Attendance Management Software',
}

ISS_CLOUD = {
    'Accounting & Billing Software Development',
    'Accounting & Bookkeeping SaaS',
    'Accounting Software (Tally, QuickBooks, Zoho Books)',
    'Audit & Documentation Solutions', 'Audit Trail Reports & Record Logs',
    'Automated Billing & Invoicing Systems',
    'Biometric Login & Authentication Systems',
    'Business Intelligence & Analytics Platforms',
    'Cloud Storage & File Sharing Services', 'Cloud Storage Subscriptions',
    'Custom Software Development', 'Data Backup & Recovery Solutions',
    'Data Encryption & Cybersecurity Solutions',
    'Desktop Application Development', 'Developer Tools (IDE, GitHub, JetBrains)',
    'Document Management & E-signature Tools',
    'Electronic Signature Software', 'Email & SMS Reminder Tools',
    'Embedded Software Development Tools',
    'Encrypted File Transmission Systems', 'Enterprise Software Solutions',
    'Facility Management Software', 'ID Card Design Software',
    'Laptop & Desktop Leasing', 'Office Productivity Software (MS Office, Google Workspace)',
    'Operating System Licenses (Windows, Linux)',
    'Order Processing & Fulfillment Systems',
    'Product Lifecycle Management (PLM) Software',
    'Project Management & Collaboration Tools',
    'SaaS Product Development', 'Secure Document Sharing & Workflow Automation',
    'Smartwatch App Development Services',
    'Software Development Consulting', 'Software Maintenance & Support',
    'Speech Recognition AI Tools', 'Training App Development Services',
    'Video Conferencing Software (Zoom, Teams, Webex)',
    'Virtual Classrooms & Meeting Rooms', 'Web Application Development',
    'Website & Landing Page Builders', 'Workflow Automation Software',
}

ISS_CREATIVE = {
    'Audio Plugins & Effects', 'DJ Software & Licenses',
    'Digital Audio Workstations (DAWs)', 'Enterprise VR Platforms',
    'Music Production Software', 'Retail & E-commerce VR Solutions',
    'Streaming Software Licenses', 'VR App Development Services',
    'VR Data Analytics Tools', 'VR Game Titles & Software',
    'VR Integration Services', 'AR-based Educational Games',
}

ISS_FLEET = {
    'API Integration for Fleet Management', 'Digital Twin Services For Vehicles',
    'Digital Vehicle Inspection Software', 'Driver Behavior Monitoring Systems',
    'EV Charging Software & Platforms', 'Electric Vehicle (Ev) Design',
    'Fleet Compliance & Documentation Tools', 'Fleet Data Reporting & Insights',
    'Fleet Lifecycle Management Software', 'Fleet Maintenance Scheduling Tools',
    'Fleet Management Software', 'Fleet Performance Analytics',
    'Fleet Route Optimization Tools', 'Fleet Tracking Software',
    'Fuel Tanks & Fuel Management Systems', 'Gps Tracking Software',
    'Mobile Apps for Fleet Control', 'OEM Fleet Software Integrations',
    'Telematics Solutions', 'Ux/UI Design For Infotainment Systems',
    'Vehicle Diagnostic Software', 'Vehicle Dispatch Software',
    'Vr/Ar-Based Auto Design Tools', '3D Cad Design For Vehicles',
    '3D Vehicle Rendering Services', 'Automobile Design Software Solutions',
    'Automotive Cfd/cae Simulation',
}

ISS_ENGINEERING = {
    '3D Imaging & Reconstruction Tools', '3D Slicing Software',
    '3D Virtual Prototyping', 'AI-based Predictive Maintenance Tools',
    'API Development & Integration', 'Automation Software & Platforms',
    'Barcode & QR Code-Based Sample Tracking', 'Barcode & RFID Tagging Systems',
    'Barcode Label Design Software', 'Batching Software & Reporting Tools',
    'Build Preparation Software', 'CAD & 3D Design Software (AutoCAD, SolidWorks)',
    'CNC Cutting Software & Controllers', 'Casting Simulation Software',
    'Design Software (Adobe CC, CorelDRAW)', 'ERP Software Development',
    'ERP Software Licenses', 'Export Documentation & Compliance Software',
    'Label Design Software', 'Programming Cables & Software',
    'Robotic Simulation Software', 'STL Editing Tools',
    'WHO PQS Certified Equipment', 'Wearable Device Repair Services',
    'Antivirus & Security Software', 'AI-Based Crop Advisory System Setup',
    'Agri ERP Software Implementation', 'Apparel Inventory Tracking Software',
    'Dealership Management Software', 'Farm Automation Planning',
    'IoT-Based Farm Management Systems', 'Multi-Warehouse Apparel Management Software',
    'Textile CAD/CAM Systems',
}

ISS_APPAREL_SW = {
    'Apparel Inventory Tracking Software': 'ERP & Business Management Software',
    'Multi-Warehouse Apparel Management Software': 'ERP & Business Management Software',
    'Textile CAD/CAM Systems': 'ERP & Business Management Software',
    'Buyer Order Tracking Portals': 'CRM & Sales Automation Software',
}

# ============================================================
# CONSTRUCTION ENGINEERING REMAP
# ============================================================
CONSTRUCTION_ENG_REMAP = {
    # Sports construction → Construction & Infrastructure with specific subcategory
    'Badminton Court Construction': ('Construction & Infrastructure', 'Sports & Recreational Infrastructure'),
    'Basketball Court Construction': ('Construction & Infrastructure', 'Sports & Recreational Infrastructure'),
    'Cricket Ground Development': ('Construction & Infrastructure', 'Sports & Recreational Infrastructure'),
    'Dugout & Players\' Benches Installation': ('Construction & Infrastructure', 'Sports & Recreational Infrastructure'),
    'Fencing & Boundary Netting': ('Construction & Infrastructure', 'Sports & Recreational Infrastructure'),
    'Football Field Construction': ('Construction & Infrastructure', 'Sports & Recreational Infrastructure'),
    'Hockey Field Installation': ('Construction & Infrastructure', 'Sports & Recreational Infrastructure'),
    'Indoor Sports Hall Construction': ('Construction & Infrastructure', 'Sports & Recreational Infrastructure'),
    'Locker Room & Shower Facilities': ('Construction & Infrastructure', 'Sports & Recreational Infrastructure'),
    'Multi-sport Arena Construction': ('Construction & Infrastructure', 'Sports & Recreational Infrastructure'),
    'Natural Grass Field Development': ('Construction & Infrastructure', 'Sports & Recreational Infrastructure'),
    'Running Track Construction': ('Construction & Infrastructure', 'Sports & Recreational Infrastructure'),
    'Skating Rink Installation': ('Construction & Infrastructure', 'Sports & Recreational Infrastructure'),
    'Squash Court Construction': ('Construction & Infrastructure', 'Sports & Recreational Infrastructure'),
    'Stadium Seating Installation': ('Construction & Infrastructure', 'Sports & Recreational Infrastructure'),
    'Swimming Pool Construction': ('Construction & Infrastructure', 'Sports & Recreational Infrastructure'),
    'Synthetic Turf Installation': ('Construction & Infrastructure', 'Sports & Recreational Infrastructure'),
    'Tennis Court Construction': ('Construction & Infrastructure', 'Sports & Recreational Infrastructure'),
    'Volleyball Court Construction': ('Construction & Infrastructure', 'Sports & Recreational Infrastructure'),
    'Sports Flooring Installation (PVC, Wooden, PU)': ('Construction & Infrastructure', 'Tiles, Marble, Granite & Flooring'),
    'Sports Lighting Systems': ('Electrical & Electronics', 'Lighting Fixtures & Fittings'),
    'Scoreboard & Display Installation': ('Electrical & Electronics', 'Surveillance & Security Systems'),
    'Gym & Fitness Center Setup': ('Services & Support', 'Engineering & Technical Services'),
    # Calibration → Services & Support
    '3D Scanning & Reverse Engineering': ('Services & Support', 'Engineering & Technical Services'),
    'Dimensional Calibration Services': ('Services & Support', 'Engineering & Technical Services'),
    'Electrical Instrument Calibration Tools': ('Services & Support', 'Engineering & Technical Services'),
    'Energy Audits & Power Quality Analysis': ('Services & Support', 'Engineering & Technical Services'),
    'Erection Supervision': ('Services & Support', 'Engineering & Technical Services'),
    'Flow Meter Calibration': ('Services & Support', 'Engineering & Technical Services'),
    'Gas Detector Calibration': ('Services & Support', 'Engineering & Technical Services'),
    'Green Building Consulting': ('Services & Support', 'Environmental Consulting & Audits'),
    'Humidity Calibration Services': ('Services & Support', 'Engineering & Technical Services'),
    'Maintenance Engineering Audits': ('Services & Support', 'Engineering & Technical Services'),
    'Mass Calibration Services': ('Services & Support', 'Engineering & Technical Services'),
    'Project Cost Estimation': ('Services & Support', 'Engineering & Technical Services'),
    'Prototype Manufacturing Support': ('Services & Support', 'Engineering & Technical Services'),
    'SOP & Safety Documentation Services': ('Services & Support', 'Certification & Compliance Services'),
    'Sheet Metal Fabrication Consulting': ('Services & Support', 'Engineering & Technical Services'),
    'Solar Power Plant Design': ('Services & Support', 'Engineering & Technical Services'),
    'Temperature Calibration Services': ('Services & Support', 'Engineering & Technical Services'),
    'Torque Wrench Calibration': ('Services & Support', 'Engineering & Technical Services'),
    'Water Conservation Engineering': ('Services & Support', 'Engineering & Technical Services'),
    'Weighing Scale Calibration': ('Services & Support', 'Engineering & Technical Services'),
}

# ============================================================
# SPECIFIC FIXES
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
    ('Office Supplies & Equipment', 'Computer Accessories'): ('Electrical & Electronics', 'Computer Accessories'),
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

    logger.info('Starting Phase 5 — Validator v8')

    input_path = os.path.join(PHASE4_OUTPUT_DIR, 'normalized.csv')
    if not os.path.exists(input_path):
        raise FileNotFoundError(f'Phase 4 output not found: {input_path}')

    df = pd.read_csv(input_path)
    if 'attributes' in df.columns:
        df = df.drop(columns=['attributes'])

    initial = len(df)
    logger.info(f'Input rows: {initial}')
    rows_to_delete = []

    # ── Rename Agriculture & Food Products → Agriculture & Farming
    afp_mask = df['category'] == 'Agriculture & Food Products'
    df.loc[afp_mask, 'category'] = 'Agriculture & Farming'
    logger.info(f'Renamed Agriculture & Food Products → Agriculture & Farming: {afp_mask.sum()} rows')

    # ── Delete Excess Inventory
    excess_mask = df['subcategory'] == 'Excess Inventory'
    rows_to_delete.extend(df[excess_mask].index.tolist())
    logger.info(f'Marked {excess_mask.sum()} Excess Inventory rows for deletion')

    # ── Issue 9: Delete truncated/invalid
    delete_mask = df['product_category'].isin(PRODUCTS_TO_DELETE)
    rows_to_delete.extend(df[delete_mask].index.tolist())
    logger.info(f'Issue 9: Marked {delete_mask.sum()} invalid products for deletion')

    # ── Issue 1: Move food products to Food & Beverage
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

    # ── Fix 1: Move food subcategories from Agriculture & Farming to Food & Beverage
    agri_food_mask = (
        (df['category'] == 'Agriculture & Farming') &
        (df['subcategory'].isin(FOOD_SUBCATEGORIES_IN_AGRI))
    )
    agri_food_count = agri_food_mask.sum()
    if agri_food_count:
        df.loc[agri_food_mask, 'category'] = 'Food & Beverage'
        logger.info(f'Fix 1: Moved {agri_food_count} food subcategory products from Agriculture to Food & Beverage')

    # ── Fix 2: Garment Manufacturing (OEM/ODM) → correct apparel subcategories
    gm_mask = df['subcategory'] == 'Garment Manufacturing (OEM/ODM)'
    gm_fixed = 0
    for idx, row in df[gm_mask].iterrows():
        prod = row['product_category']
        new_sub = GARMENT_OEM_REMAP.get(prod, "Men's Wear")
        df.at[idx, 'subcategory'] = new_sub
        gm_fixed += 1
    logger.info(f'Fix 2: Garment Manufacturing (OEM/ODM) — {gm_fixed} products remapped')

    # ── Fix 3: Industry-Specific Software reclassification
    iss_mask = (
        (df['category'] == 'Software & IT Solutions') &
        (df['subcategory'] == 'Industry-Specific Software')
    )
    iss_fixed = 0
    for idx, row in df[iss_mask].iterrows():
        prod = row['product_category']
        if prod in ISS_HEALTHCARE:
            df.at[idx, 'subcategory'] = 'Healthcare IT Software'
            iss_fixed += 1
        elif prod in ISS_IOT:
            df.at[idx, 'subcategory'] = 'IoT & Smart Building Software'
            iss_fixed += 1
        elif prod in ISS_CRM:
            df.at[idx, 'subcategory'] = 'CRM & Sales Automation Software'
            iss_fixed += 1
        elif prod in ISS_HR:
            df.at[idx, 'subcategory'] = 'HR & Payroll Software'
            iss_fixed += 1
        elif prod in ISS_CLOUD:
            df.at[idx, 'subcategory'] = 'Cloud & Productivity Software'
            iss_fixed += 1
        elif prod in ISS_CREATIVE:
            df.at[idx, 'subcategory'] = 'Creative & Game Development Software'
            iss_fixed += 1
        elif prod in ISS_FLEET:
            df.at[idx, 'subcategory'] = 'Fleet & Vehicle Management Software'
            iss_fixed += 1
        elif prod in ISS_APPAREL_SW:
            df.at[idx, 'subcategory'] = ISS_APPAREL_SW[prod]
            iss_fixed += 1
    logger.info(f'Fix 3: Industry-Specific Software reclassified — {iss_fixed} products moved')

    # ── Fix 4: Construction Engineering remap
    const_eng_mask = (
        (df['category'] == 'Construction & Infrastructure') &
        (df['subcategory'] == 'Engineering & Technical Services')
    )
    const_eng_fixed = 0
    for idx, row in df[const_eng_mask].iterrows():
        prod = row['product_category']
        if prod in CONSTRUCTION_ENG_REMAP:
            new_cat, new_sub = CONSTRUCTION_ENG_REMAP[prod]
            df.at[idx, 'category'] = new_cat
            df.at[idx, 'subcategory'] = new_sub
            const_eng_fixed += 1
    logger.info(f'Fix 4: Construction Engineering remapped — {const_eng_fixed} products')

    # ── Specific fixes
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

    # ── Industrial Tools split
    it_mask = ((df['category'] == 'Machinery & Equipment') &
               (df['subcategory'] == 'Industrial Tools'))
    it_packaging_kw = ['shrink wrap', 'packing machine', 'filling machine', 'sealing machine',
        'labeling machine', 'cartoning', 'form fill seal', 'wrapping machine', 'packaging line',
        'case packer', 'coding machine', 'flow wrap', 'sleeve wrap', 'auger fill',
        'bag in box', 'carton sealer', 'heat sealing machine', 'induction seal']
    it_metal_kw = ['scrap metal', 'metal scrap', 'steel scrap', 'copper scrap', 'aluminum scrap',
        'iron scrap', 'metal coil', 'metal rod', 'stainless steel sheet', 'metal plate',
        'metal foil', 'metal baling', 'ferrous scrap', 'non-ferrous scrap']
    it_cold_kw = ['cold room', 'cold storage unit', 'refrigerated van', 'reefer container',
        'portable cold box', 'condensing unit']
    it_stage_kw = ['stage platform', 'stage riser', 'stage truss', 'dj booth', 'pipe and drape',
        'backdrop frame', 'stage canopy', 'stage curtain', 'portable stage']
    it_farm_kw = ['seed dibbler', 'seed grader', 'direct seeder', 'soil auger',
        'agricultural crate', 'farm trailer', 'fertilizer spreader', 'transplanter',
        'brush cutter', 'polyhouse', 'venturi injector']
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
    logger.info(f'Industrial Tools split — {it_reclassified} products reclassified')

    # ── Apply deletions
    df = df.drop(index=list(set(rows_to_delete)))
    logger.info(f'Total rows deleted: {len(set(rows_to_delete))}')

    # ── Software misplacement
    misplaced_mask = df.apply(
        lambda row: row['category'] in NON_SOFTWARE_CATEGORIES
                    and is_software(str(row['product_category'])), axis=1)
    if misplaced_mask.sum():
        logger.warning(f'Misplaced software auto-corrected: {misplaced_mask.sum()}')
        df.loc[misplaced_mask, 'category'] = 'Software & IT Solutions'
        df.loc[misplaced_mask, 'subcategory'] = 'Industry-Specific Software'

    # ── Deduplication
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

    # ── Drop empty
    df = df.dropna(subset=['category', 'subcategory', 'product_category'])
    df = df[df['product_category'].str.strip() != '']

    # ── Sort
    df = df.sort_values(['category', 'subcategory', 'product_category']).reset_index(drop=True)

    final = len(df)
    cat_count = df['category'].nunique()
    sub_count = df['subcategory'].nunique()

    # ── Validation report
    food_bev = len(df[df['category'] == 'Food & Beverage'])
    agri = len(df[df['category'] == 'Agriculture & Farming'])
    it_remaining = len(df[(df['category'] == 'Machinery & Equipment') &
                          (df['subcategory'] == 'Industrial Tools')])
    gm_remaining = len(df[df['subcategory'] == 'Garment Manufacturing (OEM/ODM)'])
    food_in_agri = len(df[(df['category'] == 'Agriculture & Farming') &
                           (df['subcategory'].isin(FOOD_SUBCATEGORIES_IN_AGRI))])
    sw_subs = df[df['category'] == 'Software & IT Solutions']['subcategory'].value_counts()
    iss_remaining = len(df[(df['category'] == 'Software & IT Solutions') &
                            (df['subcategory'] == 'Industry-Specific Software')])

    logger.info(f'\n{"="*55}')
    logger.info('VALIDATION RESULTS:')
    logger.info(f'  Fix 1 — Food subcats in Agriculture & Farming: {food_in_agri} (target: 0)')
    logger.info(f'  Fix 2 — Garment Manufacturing (OEM/ODM) remaining: {gm_remaining} (target: 0)')
    logger.info(f'  Fix 3 — Industry-Specific Software remaining: {iss_remaining} (target: <50)')
    logger.info(f'  Fix 4 — Industrial Tools remaining: {it_remaining} (was 461)')
    logger.info(f'  Food & Beverage: {food_bev} products')
    logger.info(f'  Agriculture & Farming: {agri} products')
    logger.info(f'{"="*55}')
    logger.info(f'\nSoftware subcategories:\n{sw_subs.to_string()}')
    logger.info(f'\nCategory distribution:\n{df["category"].value_counts().to_string()}')

    set_metric('final_products', final)
    set_metric('final_subcategories', sub_count)
    set_metric('final_categories', cat_count)
    set_metric('food_beverage_products', food_bev)
    set_metric('agriculture_farming_products', agri)
    set_metric('industrial_tools_remaining', it_remaining)
    set_metric('garment_oem_remaining', gm_remaining)
    set_metric('iss_remaining', iss_remaining)

    output_path = os.path.join(PHASE5_OUTPUT_DIR, 'final_taxonomy.csv')
    df.to_csv(output_path, index=False, encoding='utf-8')
    logger.info(f'Output: {output_path} ({final} rows | {sub_count} subcategories | {cat_count} categories)')

    save_metrics()
    mark_completed('phase5')
    logger.info('Phase 5 complete.')

if __name__ == '__main__':
    run()
