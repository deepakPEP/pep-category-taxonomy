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
# FIX A — Redistribute Agriculture & Food Products leftover
# Every subcategory mapped to its correct category + subcategory
# ============================================================
FIX_A_REMAP = {
    # Baking Ingredients → Food & Beverage
    'Baking Ingredients': ('Food & Beverage', 'Bakery & Confectionery Products'),

    # Certification Services → Services & Support
    'Certification Services': ('Services & Support', 'Certification & Compliance Services'),

    # Excess Inventory → DELETE (not a product type)
    'Excess Inventory': None,

    # Food Grade Packaging → Packaging & Printing
    'Food Grade Packaging': ('Packaging & Printing', 'Food Grade Packaging'),

    # Food Processing Machinery → Machinery & Equipment
    'Food Processing Machinery': ('Machinery & Equipment', 'Food Processing Machinery'),

    # Gardening Tools → Tools & Hardware
    'Gardening Tools': ('Tools & Hardware', 'Gardening Tools'),

    # Manufacturing Services → Services & Support
    'Manufacturing Services': ('Services & Support', 'Contract Manufacturing Services'),

    # Poultry Farming Services → Services & Support
    'Poultry Farming Services': ('Services & Support', 'Agricultural & Farming Services'),

    # Sports Nutrition & Supplements → Health & Personal Care
    'Sports Nutrition & Supplements': ('Health & Personal Care', 'Health Supplements & Nutraceuticals'),

    # Tobacco & Smoking Products → Food & Beverage
    'Tobacco & Smoking Products': ('Food & Beverage', 'Tobacco & Smoking Products'),

    # Training & Capacity Building → Services & Support
    'Training & Capacity Building': ('Services & Support', 'Training & Skill Development'),
}

# ============================================================
# FIX B — Remove Energy & Power category (too few products)
# Remap 3 products to correct categories
# ============================================================
FIX_B_ENERGY_REMAP = {
    'Biogas Plant Machinery': ('Machinery & Equipment', 'Renewable Energy Machinery'),
    'Solar Energy Monitoring Systems': ('Software & IT Solutions', 'IoT & Smart Building Software'),
    'Wind Turbine Commissioning': ('Services & Support', 'Engineering & Technical Services'),
}

# ============================================================
# FIX C — Reclassify ERP overload (228 products → correct subcategories)
# Exact product → correct subcategory mapping
# ============================================================
FIX_C_PRODUCT_SUBCATEGORY = {
    # → Creative & Game Development Software
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

    # → IoT & Smart Building Software
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

    # → CRM & Sales Automation Software
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

    # → HR & Payroll Software
    'Attendance & HRMS Software': 'HR & Payroll Software',
    'Biometric Attendance Systems': 'HR & Payroll Software',
    'HR & Payroll Management Software': 'HR & Payroll Software',
    'HRMS & Payroll Integration Services': 'HR & Payroll Software',
    'Human Resource Management Systems (HRMS)': 'HR & Payroll Software',
    'Payroll Software Solutions': 'HR & Payroll Software',
    'Time & Attendance Management Software': 'HR & Payroll Software',

    # → Healthcare IT Software
    'Cloud-Based Medical Transcription Tools': 'Healthcare IT Software',
    'Diagnostic Software & Scanners': 'Healthcare IT Software',
    'Go-To-Market Strategy for Wellness Brands': 'Healthcare IT Software',
    'Healthcare Startup Business Strategy': 'Healthcare IT Software',
    'Hospital Information Management Systems (HIMS)': 'Healthcare IT Software',
    'Medical Billing Software Solutions': 'Healthcare IT Software',
    'Medical VR Equipment': 'Healthcare IT Software',

    # → Industry-Specific Software
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

    # → Cloud & Productivity Software
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

    # → ERP & Business Management Software (genuine ERP products — keep)
    'Apparel Business Intelligence Tools': 'ERP & Business Management Software',
    'Apparel Dropshipping Management Software': 'ERP & Business Management Software',
    'Business Intelligence & Analytics Platforms': 'ERP & Business Management Software',
    'Custom ERP for Fashion Brands': 'ERP & Business Management Software',
    'E-commerce Integrated ERP (Shopify, WooCommerce)': 'ERP & Business Management Software',
    'ERP Integration Services for Garment': 'ERP & Business Management Software',
    'ERP Software Licenses': 'ERP & Business Management Software',
    'Enterprise Resource Planning (ERP) Tools': 'ERP & Business Management Software',
    'Enterprise Software Solutions': 'ERP & Business Management Software',
    'Erp Software Development': 'ERP & Business Management Software',
    'Facility Management Software': 'ERP & Business Management Software',
    'Fashion Design & Development ERP': 'ERP & Business Management Software',
    'Garment Manufacturing ERP Software': 'ERP & Business Management Software',
    'Inventory Management Software': 'ERP & Business Management Software',
    'Inventory Management Software for Apparel': 'ERP & Business Management Software',
    'Mobile ERP Solutions for Apparel Units': 'ERP & Business Management Software',
    'Multi-Warehouse Apparel Management Software': 'ERP & Business Management Software',
    'Multi-channel Retail ERP Solutions': 'ERP & Business Management Software',
    'Online Fitness Program Marketplaces': 'ERP & Business Management Software',
    'Online Trophy Customization Tools': 'ERP & Business Management Software',
    'Order Processing & Fulfillment Systems': 'ERP & Business Management Software',
    'Product Lifecycle Management (Plm) Software': 'ERP & Business Management Software',
    'Production Status Monitoring ERP': 'ERP & Business Management Software',
    'Raw Material Management ERP': 'ERP & Business Management Software',
    'Stock Replenishment & Forecasting Tools': 'ERP & Business Management Software',
    'Textile Cad/Cam Systems': 'ERP & Business Management Software',
    'Textile Production ERP Systems': 'ERP & Business Management Software',
    'Vendor Management Software for Apparel': 'ERP & Business Management Software',

    # Toys — move to Home & Lifestyle
    'Augmented Reality (AR) Toys': None,  # → Home & Lifestyle
    'Baby Monitors': None,
    'Digital Flashcards': None,
    'Electronic Board Games': None,
    'Electronic Building Blocks': None,
    'Electronic Drawing Pads': None,
    'Kids\' Tablets & Learning Pads': None,
    'Language Learning Devices': None,
    'Musical Toys': None,
    'Remote-Controlled Educational Bots': None,
    'Sound and Light Toys': None,

    # PCB Assembly — move to Electrical & Electronics
    'Box Build Assembly': None,
    'Conformal Coating Services': None,
    'Custom Electronic Assembly Services': None,
    'High Volume PCB Assembly': None,
    'Mixed Technology Assembly': None,
    'PCB Soldering Services': None,
    'PCBA Testing & Quality Control': None,
    'Prototype PCB Assembly': None,
    'Reflow Soldering Services': None,
    'Surface Mount Technology (SMT) Assembly': None,
    'Through-Hole Assembly Services': None,
    'Turnkey PCB Assembly Services': None,
    'Wave Soldering Services': None,
    'X-Ray Inspection For PCBAs': None,

    # Misc wrong
    'Barcode Labels For Waste Bags': None,  # → Packaging & Printing
    'Barcode & RFID Tagging Systems': None,  # → Packaging & Printing
    'Ink Supplies': None,  # → Packaging & Printing
    'Lighting Design Consultants': None,  # → Services & Support
    'Operator Training Programs': None,  # → Services & Support
}

# For products with None — their correct destination
FIX_C_PRODUCT_CATEGORY_DEST = {
    'Augmented Reality (AR) Toys': ('Home & Lifestyle', 'Children\'s Play Equipment & Toys'),
    'Baby Monitors': ('Home & Lifestyle', 'Children\'s Play Equipment & Toys'),
    'Digital Flashcards': ('Home & Lifestyle', 'Children\'s Play Equipment & Toys'),
    'Electronic Board Games': ('Home & Lifestyle', 'Children\'s Play Equipment & Toys'),
    'Electronic Building Blocks': ('Home & Lifestyle', 'Children\'s Play Equipment & Toys'),
    'Electronic Drawing Pads': ('Home & Lifestyle', 'Children\'s Play Equipment & Toys'),
    'Kids\' Tablets & Learning Pads': ('Home & Lifestyle', 'Children\'s Play Equipment & Toys'),
    'Language Learning Devices': ('Home & Lifestyle', 'Children\'s Play Equipment & Toys'),
    'Musical Toys': ('Home & Lifestyle', 'Children\'s Play Equipment & Toys'),
    'Remote-Controlled Educational Bots': ('Home & Lifestyle', 'Children\'s Play Equipment & Toys'),
    'Sound and Light Toys': ('Home & Lifestyle', 'Children\'s Play Equipment & Toys'),
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
    'Electronic Components': 'Industry-Specific Software',   # Music Production Software
    'Fleet Management Solutions': 'Industry-Specific Software',  # Fleet Software Integrations
    'Medical Consumables': 'Healthcare IT Software',              # Ambulance Fleet Mgmt
    'Packaging Materials': 'Industry-Specific Software',          # Barcode Label Design Software
    'Retail Point of Sale (POS) Software': 'CRM & Sales Automation Software',
    'Healthcare IT Solutions': 'Healthcare IT Software',
    'Embedded Systems Development': 'Industry-Specific Software',
}

# ============================================================
# FIX E — Sports construction → correct categories
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

# ============================================================
# SOFTWARE DETECTION (refined)
# ============================================================
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

    logger.info('Starting Phase 5 — Validator v4')

    input_path = os.path.join(PHASE4_OUTPUT_DIR, 'normalized.csv')
    if not os.path.exists(input_path):
        raise FileNotFoundError(f'Phase 4 output not found: {input_path}')

    df = pd.read_csv(input_path)
    # Drop attributes column if present — not needed yet
    if 'attributes' in df.columns:
        df = df.drop(columns=['attributes'])

    initial = len(df)
    logger.info(f'Input rows: {initial}')

    # ── FIX A: Redistribute Agriculture & Food Products leftover ─
    afp_mask = df['category'] == 'Agriculture & Food Products'
    afp_count = afp_mask.sum()
    logger.info(f'Fix A: Processing {afp_count} Agriculture & Food Products leftover rows')

    rows_to_delete = []
    for idx, row in df[afp_mask].iterrows():
        sub = row['subcategory']
        if sub not in FIX_A_REMAP:
            # Default — merge into Agriculture & Farming
            df.at[idx, 'category'] = 'Agriculture & Farming'
            continue
        dest = FIX_A_REMAP[sub]
        if dest is None:
            rows_to_delete.append(idx)
        else:
            df.at[idx, 'category'] = dest[0]
            df.at[idx, 'subcategory'] = dest[1]

    if rows_to_delete:
        df = df.drop(index=rows_to_delete)
        logger.info(f'Fix A: Deleted {len(rows_to_delete)} Excess Inventory rows')
    logger.info(f'Fix A: Agriculture & Food Products category eliminated')

    # ── FIX B: Remove Energy & Power — remap 3 products ─────────
    energy_mask = df['category'] == 'Energy & Power'
    energy_count = energy_mask.sum()
    logger.info(f'Fix B: Remapping {energy_count} Energy & Power products')
    for idx, row in df[energy_mask].iterrows():
        prod = row['product_category']
        if prod in FIX_B_ENERGY_REMAP:
            new_cat, new_sub = FIX_B_ENERGY_REMAP[prod]
            df.at[idx, 'category'] = new_cat
            df.at[idx, 'subcategory'] = new_sub
        else:
            df.at[idx, 'category'] = 'Electrical & Electronics'
            df.at[idx, 'subcategory'] = 'Renewable Energy Equipment'
    logger.info('Fix B: Energy & Power category eliminated')

    # ── FIX C: Reclassify ERP overload ──────────────────────────
    erp_mask = (
        (df['category'] == 'Software & IT Solutions') &
        (df['subcategory'] == 'ERP & Business Management Software')
    )
    erp_count = erp_mask.sum()
    logger.info(f'Fix C: Reclassifying {erp_count} ERP overload products')

    rows_to_update = []
    for idx, row in df[erp_mask].iterrows():
        prod = row['product_category']
        if prod in FIX_C_PRODUCT_SUBCATEGORY:
            new_sub = FIX_C_PRODUCT_SUBCATEGORY[prod]
            if new_sub is None:
                # Move to different category entirely
                if prod in FIX_C_PRODUCT_CATEGORY_DEST:
                    new_cat, new_sub2 = FIX_C_PRODUCT_CATEGORY_DEST[prod]
                    df.at[idx, 'category'] = new_cat
                    df.at[idx, 'subcategory'] = new_sub2
            else:
                df.at[idx, 'subcategory'] = new_sub
    logger.info('Fix C: ERP overload reclassified')

    # ── FIX D: Rename invalid software subcategories ─────────────
    sw_mask = df['category'] == 'Software & IT Solutions'
    for idx, row in df[sw_mask].iterrows():
        sub = row['subcategory']
        if sub in FIX_D_SUBCATEGORY_RENAME:
            df.at[idx, 'subcategory'] = FIX_D_SUBCATEGORY_RENAME[sub]
    logger.info('Fix D: Invalid software subcategory names corrected')

    # ── FIX E: Move sports construction to correct categories ─────
    sports_eng_mask = (
        (df['category'] == 'Sports & Entertainment') &
        (df['subcategory'] == 'Engineering & Technical Services')
    )
    sports_eng_count = sports_eng_mask.sum()
    logger.info(f'Fix E: Remapping {sports_eng_count} sports construction products')
    for idx, row in df[sports_eng_mask].iterrows():
        prod = row['product_category']
        if prod in FIX_E_SPORTS_CONSTRUCTION:
            new_cat, new_sub = FIX_E_SPORTS_CONSTRUCTION[prod]
            df.at[idx, 'category'] = new_cat
            df.at[idx, 'subcategory'] = new_sub
        else:
            df.at[idx, 'category'] = 'Construction & Infrastructure'
            df.at[idx, 'subcategory'] = 'Sports & Recreational Infrastructure'
    logger.info('Fix E: Sports construction products moved')

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

    # Final validation checks
    remaining_afp = len(df[df['category'] == 'Agriculture & Food Products'])
    remaining_energy = len(df[df['category'] == 'Energy & Power'])
    sw_subs = df[df['category'] == 'Software & IT Solutions']['subcategory'].value_counts()
    sports_eng = len(df[(df['category'] == 'Sports & Entertainment') &
                        (df['subcategory'] == 'Engineering & Technical Services')])
    erp_remaining = len(df[(df['category'] == 'Software & IT Solutions') &
                           (df['subcategory'] == 'ERP & Business Management Software')])

    logger.info(f'\n{"="*50}')
    logger.info(f'VALIDATION RESULTS:')
    logger.info(f'  Agriculture & Food Products leftover: {remaining_afp} (target: 0)')
    logger.info(f'  Energy & Power remaining: {remaining_energy} (target: 0)')
    logger.info(f'  ERP overload remaining: {erp_remaining} (target: <50)')
    logger.info(f'  Sports Engineering & Technical Services: {sports_eng} (target: 0)')
    logger.info(f'{"="*50}')

    logger.info(f'\nSoftware & IT Solutions subcategories:\n{sw_subs.to_string()}')
    logger.info(f'\nCategory distribution:\n{df["category"].value_counts().to_string()}')

    set_metric('final_products', final)
    set_metric('final_subcategories', sub_count)
    set_metric('final_categories', cat_count)
    set_metric('fix_a_afp_remaining', remaining_afp)
    set_metric('fix_b_energy_remaining', remaining_energy)
    set_metric('fix_c_erp_remaining', erp_remaining)
    set_metric('fix_e_sports_eng_remaining', sports_eng)

    output_path = os.path.join(PHASE5_OUTPUT_DIR, 'final_taxonomy.csv')
    df.to_csv(output_path, index=False, encoding='utf-8')
    logger.info(f'Final taxonomy: {output_path} ({final} rows | {sub_count} subcategories | {cat_count} categories)')

    save_metrics()
    mark_completed('phase5')
    logger.info('Phase 5 complete.')

if __name__ == '__main__':
    run()
