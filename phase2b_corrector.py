import os
import pandas as pd
from common.config import PHASE2_OUTPUT_DIR
from common.logger import get_logger
from common.checkpoint import is_completed, mark_completed

logger = get_logger("phase2b")

# ============================================================
# CANONICAL 16 CATEGORIES
# ============================================================
CANONICAL_CATEGORIES = {
    "apparel & fashion": "Apparel & Fashion",
    "agriculture & food products": "Agriculture & Food Products",
    "food & agriculture": "Agriculture & Food Products",
    "automotive & transport": "Automotive & Transport",
    "chemicals": "Chemicals & Raw Materials",
    "chemicals & raw materials": "Chemicals & Raw Materials",
    "raw materials & chemicals": "Chemicals & Raw Materials",
    "industrial gases": "Chemicals & Raw Materials",
    "construction & infrastructure": "Construction & Infrastructure",
    "construction": "Construction & Infrastructure",
    "construction materials": "Construction & Infrastructure",
    "construction services": "Services & Support",
    "electrical & electronics": "Electrical & Electronics",
    "electronics & electrical": "Electrical & Electronics",
    "health & personal care": "Health & Personal Care",
    "home & lifestyle": "Home & Lifestyle",
    "home & office appliances": "Home & Lifestyle",
    "machinery & equipment": "Machinery & Equipment",
    "industrial equipment & machinery": "Machinery & Equipment",
    "office supplies & equipment": "Office Supplies & Equipment",
    "packaging & printing": "Packaging & Printing",
    "food & beverage packaging": "Packaging & Printing",
    "services & support": "Services & Support",
    "services": "Services & Support",
    "business services": "Services & Support",
    "professional services": "Services & Support",
    "software & it solutions": "Software & IT Solutions",
    "software & its solutions": "Software & IT Solutions",
    "sports & entertainment": "Sports & Entertainment",
    "tools & hardware": "Tools & Hardware",
    "textiles & fabrics": "Apparel & Fashion",
    "textile raw materials": "Apparel & Fashion",
    "education & training": "Services & Support",
    "education": "Services & Support",
    "energy & power": "Energy & Power",
    "energy": "Energy & Power",
    "renewable energy": "Energy & Power",
}

# ============================================================
# SOFTWARE SUBCATEGORY CANONICAL MAP
# Maps any software-related subcategory to correct type-based name
# These are PRODUCT subcategories — licensed software products only
# ============================================================
SOFTWARE_SUBCATEGORY_MAP = {
    # ERP & Business Management
    "Apparel Management Software": "ERP & Business Management Software",
    "Fashion Retail POS Systems": "ERP & Business Management Software",
    "Enterprise Resource Planning (ERP)": "ERP & Business Management Software",
    "Product Lifecycle Management (PLM)": "ERP & Business Management Software",
    "Quality Management Software": "ERP & Business Management Software",
    "Quality Control Software": "ERP & Business Management Software",
    "Compliance Management Software": "ERP & Business Management Software",
    "Facility Management Software": "ERP & Business Management Software",
    "Inventory Management Software": "ERP & Business Management Software",
    "Project Management Software": "ERP & Business Management Software",
    "Business Management Software": "ERP & Business Management Software",
    "Workflow Automation Software": "ERP & Business Management Software",
    "Manufacturing Execution Systems (MES)": "ERP & Business Management Software",
    "Retail Point of Sale (POS) Software": "ERP & Business Management Software",

    # CRM & Sales Automation
    "CRM & Sales Automation": "CRM & Sales Automation Software",

    # HR & Payroll
    "HR & Payroll Software": "HR & Payroll Software",

    # Healthcare IT
    "Healthcare IT Solutions": "Healthcare IT Software",
    "Mental Health & Wellness Software": "Healthcare IT Software",
    "Digital Health & Wellness Software": "Healthcare IT Software",
    "Telehealth Devices & Software": "Healthcare IT Software",

    # Industry-Specific
    "Fleet Management Software": "Industry-Specific Software",
    "Agriculture Software": "Industry-Specific Software",
    "Industrial Automation Software": "Industry-Specific Software",
    "Industrial Software": "Industry-Specific Software",
    "Industrial Control Systems": "Industry-Specific Software",
    "EV Software & Platforms": "Industry-Specific Software",
    "Simulation & Modeling Software": "Industry-Specific Software",
    "Electronic Design Automation (EDA)": "Industry-Specific Software",
    "3D Printing Software": "Industry-Specific Software",
    "Engineering & Design Software": "Industry-Specific Software",
    "STEM Software": "Industry-Specific Software",

    # Cloud & Productivity
    "Data Backup & Disaster Recovery": "Cloud & Productivity Software",
    "Cloud & Productivity Software": "Cloud & Productivity Software",
    "Custom Software Development": "Cloud & Productivity Software",

    # IoT & Smart Building
    "Building Management Systems": "IoT & Smart Building Software",
    "Energy Management Systems": "IoT & Smart Building Software",

    # Educational
    "Educational Software": "Educational & eLearning Software",

    # Cybersecurity
    "Cybersecurity Software": "Cybersecurity Software",

    # Game Development
    "Game Development Software": "Creative & Game Development Software",
    "AR/VR Development Software": "Creative & Game Development Software",

    # SERVICES that were wrongly in Software — move to Services & Support
    # These will be handled by SUBCATEGORY_CATEGORY_REMAP below
    "Digital Marketing Services": None,  # → Services & Support
    "Mobile App Development": None,       # → Services & Support
    "Translation & Localization Services": None,  # → Services & Support
    "Digital Imaging Services": None,     # → Services & Support
}

# ============================================================
# SUBCATEGORY → CORRECT CATEGORY REMAP
# ============================================================
SUBCATEGORY_CATEGORY_REMAP = {
    # Agriculture wrongly placed
    "Leather & Hides": "Apparel & Fashion",
    "Textile Raw Materials": "Apparel & Fashion",
    "Recycled Apparel": "Apparel & Fashion",
    "Fashion Design Services": "Services & Support",
    "Timber & Logs": "Construction & Infrastructure",
    "Wood & Wood Products": "Construction & Infrastructure",
    "Processed Wood": "Construction & Infrastructure",
    "Biodegradable & Sustainable Raw Materials": "Chemicals & Raw Materials",

    # Electrical wrongly placed
    "Tiles, Marble, Granite & Flooring": "Construction & Infrastructure",
    "Sunglasses & Eyewear": "Apparel & Fashion",
    "Office Telephones & Intercom Systems": "Office Supplies & Equipment",
    "Office Supplies for Remote Work": "Office Supplies & Equipment",
    "Hydroponic & Vertical Farming Systems": "Agriculture & Food Products",
    "DJ & Studio Equipment": "Sports & Entertainment",
    "Medical Rehabilitation Equipment": "Health & Personal Care",
    "Beauty Equipment (Salon, Spa Devices)": "Health & Personal Care",
    "Kitchen Appliances": "Home & Lifestyle",
    "Vehicle Electrical Systems": "Automotive & Transport",
    "Aquaculture & Fisheries Equipment": "Machinery & Equipment",

    # Home & Lifestyle — sports wrongly placed
    "Water Sports Equipment (Swimming, Surfing, Diving)": "Sports & Entertainment",
    "Martial Arts & Boxing Equipment": "Sports & Entertainment",
    "Cycling Gear & Accessories": "Sports & Entertainment",
    "Gym Accessories (Mats, Belts, Bands)": "Sports & Entertainment",
    "Skating & Skateboarding Equipment": "Sports & Entertainment",
    "Recreational Games (Table Tennis, Pool, Carrom)": "Sports & Entertainment",
    "Trophies, Medals & Awards": "Sports & Entertainment",
    "Fan Merchandise & Collectibles": "Sports & Entertainment",
    "Talent Management & Booking Agencies": "Services & Support",
    "Entertainment Licensing & Distribution": "Services & Support",
    "Sports Facility Construction Services": "Services & Support",
    "Stage, Set & Truss Equipment": "Sports & Entertainment",
    "Team Sports Equipment (Football, Basketball, Cricket)": "Sports & Entertainment",
    "Outdoor Sports Gear (Camping, Hiking, Climbing)": "Sports & Entertainment",
    "Indoor Sports Equipment": "Sports & Entertainment",
    "Sportswear & Activewear": "Sports & Entertainment",
    "Sportswear Branding & Customization": "Sports & Entertainment",
    "Board Games & Puzzles": "Sports & Entertainment",
    "Athletic Footwear": "Sports & Entertainment",
    "Fitness Equipment (Home & Commercial)": "Sports & Entertainment",
    "Fitness & Sports Training Services": "Services & Support",
    "Yoga Accessories & Equipment": "Sports & Entertainment",
    "Musical Instruments": "Sports & Entertainment",
    "Hockey Equipment": "Sports & Entertainment",
    "Baseball Equipment": "Sports & Entertainment",
    "Volleyball Equipment": "Sports & Entertainment",
    "Board Game Accessories": "Sports & Entertainment",
    "Cricket Equipment": "Sports & Entertainment",
    "Tennis Equipment": "Sports & Entertainment",
    "Badminton Equipment": "Sports & Entertainment",
    "Children's Play Equipment & Toys": "Sports & Entertainment",

    # Machinery wrongly placed
    "Electronic Toys & Educational Toys": "Home & Lifestyle",
    "Gaming Consoles & Accessories": "Electrical & Electronics",
    "Baby Furniture": "Home & Lifestyle",
    "Home Appliances": "Electrical & Electronics",
    "Kitchen Equipment": "Home & Lifestyle",
    "Pediatric Therapy Equipment": "Health & Personal Care",
    "Gait Training Equipment": "Health & Personal Care",
    "Wellness Devices": "Health & Personal Care",
    "Fitness & Wellness Equipment": "Sports & Entertainment",
    "Heavy Duty Trucks": "Automotive & Transport",
    "Garment Accessories & Trims": "Apparel & Fashion",
    "Three-Wheelers": "Automotive & Transport",

    # Chemicals wrongly placed
    "Food Additives & Preservatives": "Agriculture & Food Products",
    "Food Additives & Ingredients": "Agriculture & Food Products",
    "Agrochemicals": "Agriculture & Food Products",
    "Agrochemicals & Biostimulants": "Agriculture & Food Products",
    "Pesticides & Crop Protection": "Agriculture & Food Products",
    "Organic Pesticides": "Agriculture & Food Products",
    "Fertilizers & Soil Conditioners": "Agriculture & Food Products",

    # Construction wrongly placed
    "Workshop Equipment": "Tools & Hardware",
    "Tool Room Equipment": "Tools & Hardware",

    # Sports wrongly placed
    "Recycling Machinery": "Machinery & Equipment",
    "Consumer Electronics": "Electrical & Electronics",

    # Software — services that don't belong in Software & IT Solutions
    "Digital Marketing Services": "Services & Support",
    "Mobile App Development": "Services & Support",
    "Translation & Localization Services": "Services & Support",
    "Digital Imaging Services": "Services & Support",
    "AR/VR Development Services": "Services & Support",

    # Software — hardware/physical that doesn't belong in Software
    "Barcode Labels & RFID Tags": "Packaging & Printing",
    "Control Panels & PLCs": "Electrical & Electronics",
    "Cold Chain Logistics & Storage": "Agriculture & Food Products",

    # Health wrongly placed
    "Restroom Furniture": "Office Supplies & Equipment",

    # Automotive duplicates
    "Vehicle Insurance And Financing": "Automotive & Transport",
    "Fleet Management Solutions": "Automotive & Transport",
    "Retreaded Tyres": "Automotive & Transport",
    "Steering Components": "Automotive & Transport",
    "Suspension Components": "Automotive & Transport",
    "Lighting & Signaling Devices": "Automotive & Transport",
}

# When a subcategory moves to a new category, what subcategory does it use?
SUBCATEGORY_REMAP_TARGET = {
    ("Leather & Hides", "Apparel & Fashion"): "Leather Materials",
    ("Textile Raw Materials", "Apparel & Fashion"): "Fabrics",
    ("Recycled Apparel", "Apparel & Fashion"): "Sustainable Apparel",
    ("Fashion Design Services", "Services & Support"): "Graphic Design & Branding",
    ("Timber & Logs", "Construction & Infrastructure"): "Wood & Plywood Products",
    ("Wood & Wood Products", "Construction & Infrastructure"): "Wood & Plywood Products",
    ("Processed Wood", "Construction & Infrastructure"): "Wood & Plywood Products",
    ("Biodegradable & Sustainable Raw Materials", "Chemicals & Raw Materials"): "Biodegradable & Sustainable Raw Materials",
    ("Tiles, Marble, Granite & Flooring", "Construction & Infrastructure"): "Tiles, Marble, Granite & Flooring",
    ("Sunglasses & Eyewear", "Apparel & Fashion"): "Accessories",
    ("Office Telephones & Intercom Systems", "Office Supplies & Equipment"): "Office Phones & Intercom Systems",
    ("Office Supplies for Remote Work", "Office Supplies & Equipment"): "Office Stationery",
    ("Hydroponic & Vertical Farming Systems", "Agriculture & Food Products"): "Hydroponic & Vertical Farming Systems",
    ("DJ & Studio Equipment", "Sports & Entertainment"): "Musical Instruments",
    ("Medical Rehabilitation Equipment", "Health & Personal Care"): "Rehabilitation & Physiotherapy Equipment",
    ("Beauty Equipment (Salon, Spa Devices)", "Health & Personal Care"): "Beauty Equipment (Salon, Spa Devices)",
    ("Kitchen Appliances", "Home & Lifestyle"): "Small Kitchen Appliances",
    ("Vehicle Electrical Systems", "Automotive & Transport"): "Vehicle Electrical Systems",
    ("Aquaculture & Fisheries Equipment", "Machinery & Equipment"): "Aquaculture & Fisheries Equipment",
    ("Water Sports Equipment (Swimming, Surfing, Diving)", "Sports & Entertainment"): "Water Sports Equipment (Swimming, Surfing, Diving)",
    ("Martial Arts & Boxing Equipment", "Sports & Entertainment"): "Martial Arts & Boxing Equipment",
    ("Cycling Gear & Accessories", "Sports & Entertainment"): "Cycling Gear & Accessories",
    ("Gym Accessories (Mats, Belts, Bands)", "Sports & Entertainment"): "Gym Accessories (Mats, Belts, Bands)",
    ("Skating & Skateboarding Equipment", "Sports & Entertainment"): "Skating & Skateboarding Equipment",
    ("Recreational Games (Table Tennis, Pool, Carrom)", "Sports & Entertainment"): "Recreational Games (Table Tennis, Pool, Carrom)",
    ("Trophies, Medals & Awards", "Sports & Entertainment"): "Trophies, Medals & Awards",
    ("Fan Merchandise & Collectibles", "Sports & Entertainment"): "Fan Merchandise & Collectibles",
    ("Talent Management & Booking Agencies", "Services & Support"): "Event Management & Promotion",
    ("Entertainment Licensing & Distribution", "Services & Support"): "Event Management & Promotion",
    ("Sports Facility Construction Services", "Services & Support"): "Engineering & Technical Services",
    ("Stage, Set & Truss Equipment", "Sports & Entertainment"): "Stage, Set & Truss Equipment",
    ("Team Sports Equipment (Football, Basketball, Cricket)", "Sports & Entertainment"): "Team Sports Equipment (Football, Basketball, Cricket)",
    ("Outdoor Sports Gear (Camping, Hiking, Climbing)", "Sports & Entertainment"): "Outdoor Sports Gear (Camping, Hiking, Climbing)",
    ("Indoor Sports Equipment", "Sports & Entertainment"): "Indoor Sports Equipment",
    ("Sportswear & Activewear", "Sports & Entertainment"): "Sportswear & Activewear",
    ("Sportswear Branding & Customization", "Sports & Entertainment"): "Sportswear Branding & Customization",
    ("Board Games & Puzzles", "Sports & Entertainment"): "Board Games & Puzzles",
    ("Athletic Footwear", "Sports & Entertainment"): "Athletic Footwear",
    ("Fitness Equipment (Home & Commercial)", "Sports & Entertainment"): "Fitness Equipment (Home & Commercial)",
    ("Fitness & Sports Training Services", "Services & Support"): "Training & Skill Development",
    ("Yoga Accessories & Equipment", "Sports & Entertainment"): "Yoga Accessories & Equipment",
    ("Musical Instruments", "Sports & Entertainment"): "Musical Instruments",
    ("Hockey Equipment", "Sports & Entertainment"): "Indoor Sports Equipment",
    ("Baseball Equipment", "Sports & Entertainment"): "Team Sports Equipment (Football, Basketball, Cricket)",
    ("Volleyball Equipment", "Sports & Entertainment"): "Team Sports Equipment (Football, Basketball, Cricket)",
    ("Board Game Accessories", "Sports & Entertainment"): "Board Games & Puzzles",
    ("Cricket Equipment", "Sports & Entertainment"): "Team Sports Equipment (Football, Basketball, Cricket)",
    ("Tennis Equipment", "Sports & Entertainment"): "Team Sports Equipment (Football, Basketball, Cricket)",
    ("Badminton Equipment", "Sports & Entertainment"): "Team Sports Equipment (Football, Basketball, Cricket)",
    ("Children's Play Equipment & Toys", "Sports & Entertainment"): "Board Games & Puzzles",
    ("Electronic Toys & Educational Toys", "Home & Lifestyle"): "Children's Play Equipment & Toys",
    ("Gaming Consoles & Accessories", "Electrical & Electronics"): "Gaming Consoles & Accessories",
    ("Baby Furniture", "Home & Lifestyle"): "Bedroom Furniture",
    ("Home Appliances", "Electrical & Electronics"): "Home Appliances",
    ("Kitchen Equipment", "Home & Lifestyle"): "Modular Kitchen Units",
    ("Pediatric Therapy Equipment", "Health & Personal Care"): "Rehabilitation & Physiotherapy Equipment",
    ("Gait Training Equipment", "Health & Personal Care"): "Rehabilitation & Physiotherapy Equipment",
    ("Wellness Devices", "Health & Personal Care"): "Health Monitoring Devices",
    ("Fitness & Wellness Equipment", "Sports & Entertainment"): "Fitness Equipment (Home & Commercial)",
    ("Heavy Duty Trucks", "Automotive & Transport"): "Commercial Vehicles",
    ("Garment Accessories & Trims", "Apparel & Fashion"): "Garment Accessories & Trims",
    ("Three-Wheelers", "Automotive & Transport"): "Two-Wheelers",
    ("Food Additives & Preservatives", "Agriculture & Food Products"): "Food Additives & Preservatives",
    ("Food Additives & Ingredients", "Agriculture & Food Products"): "Food Additives & Preservatives",
    ("Agrochemicals", "Agriculture & Food Products"): "Pesticides & Crop Protection",
    ("Agrochemicals & Biostimulants", "Agriculture & Food Products"): "Pesticides & Crop Protection",
    ("Pesticides & Crop Protection", "Agriculture & Food Products"): "Pesticides & Crop Protection",
    ("Organic Pesticides", "Agriculture & Food Products"): "Pesticides & Crop Protection",
    ("Fertilizers & Soil Conditioners", "Agriculture & Food Products"): "Fertilizers & Soil Conditioners",
    ("Workshop Equipment", "Tools & Hardware"): "Workbenches & Workshop Tools",
    ("Tool Room Equipment", "Tools & Hardware"): "Tool Storage & Organizers",
    ("Recycling Machinery", "Machinery & Equipment"): "Recycling Machinery",
    ("Consumer Electronics", "Electrical & Electronics"): "Consumer Electronics",
    ("Digital Marketing Services", "Services & Support"): "Digital Marketing Services",
    ("Mobile App Development", "Services & Support"): "Web Design & Development",
    ("Translation & Localization Services", "Services & Support"): "Translation & Localization Services",
    ("Digital Imaging Services", "Services & Support"): "Digital Marketing Services",
    ("AR/VR Development Services", "Services & Support"): "Web Design & Development",
    ("Barcode Labels & RFID Tags", "Packaging & Printing"): "Barcode Labels & RFID Tags",
    ("Control Panels & PLCs", "Electrical & Electronics"): "Control Panels & PLCs",
    ("Cold Chain Logistics & Storage", "Agriculture & Food Products"): "Cold Chain Logistics & Storage",
    ("Restroom Furniture", "Office Supplies & Equipment"): "Office Furniture",
    ("Fragrances & Essential Oils", "Chemicals & Raw Materials"): "Fragrances & Essential Oils",
    ("Industrial Gases", "Chemicals & Raw Materials"): "Industrial Gases",
}

# ============================================================
# SUBCATEGORY NAME CANONICAL MAP
# Resolves case duplicates and naming inconsistencies
# ============================================================
SUBCATEGORY_NAME_CANONICAL = {
    # Case duplicates
    "Women's personal care products": "Women's Personal Care Products",
    "Over-the-Counter Medicines": "Over-The-Counter Medicines",
    "Ethnic And Cultural Clothing": "Ethnic & Cultural Clothing",
    "Workwear & Uniforms": "Workwear / Uniforms",
    "Loungewear / Sleepwear": "Loungewear & Sleepwear",
    "Artificial Plants And Flowers": "Artificial Plants & Flowers",
    "Bath Linens And Towels": "Bath Linens & Towels",
    "Mattresses And Mattress Toppers": "Mattresses & Mattress Toppers",
    "Generators And Alternators": "Generators & Alternators",
    "Semiconductors And Integrated Circuits": "Semiconductors & ICs",
    "Circuit Breakers And Fuses": "Circuit Breakers & Fuses",
    "Ready-To-Eat & Instant Foods": "Ready-to-Eat & Instant Foods",
    "Cnc Machines": "CNC Machines",
    "Vehicle Insurance And Financing": "Vehicle Insurance & Financing",
    "HVAC Equipment (Heating, Ventilation, Air Conditioning)": "HVAC Equipment",

    # Consolidate fragmented subcategories
    "Baking Ingredients & Supplies": "Baking Ingredients",
    "Confectionery Products": "Bakery & Confectionery Products",
    "Dairy Products": "Dairy Products & Alternatives",
    "Pulses": "Grains, Cereals & Pulses",
    "Split Pulses": "Grains, Cereals & Pulses",
    "Lentils": "Grains, Cereals & Pulses",
    "Seeds": "Seeds & Planting Materials",
    "Flower Seeds": "Seeds & Planting Materials",
    "Herb Seeds": "Seeds & Planting Materials",
    "Fruit Seeds": "Seeds & Planting Materials",
    "Vegetable Seeds": "Seeds & Planting Materials",
    "Fresh Produce Export": "Agricultural Produce",
    "Essential Staples": "Grains, Cereals & Pulses",
    "Certifications": "Certification Services",
    "Packaging Formats": "Food Packaging Materials",
    "Packaging Options": "Food Packaging Materials",
    "Office Pantry Supplies": "Catering Supplies & Ingredients",
    "Fertilizers & Soil Amendments": "Fertilizers & Soil Conditioners",
    "Fruit Saplings": "Seeds & Planting Materials",

    # Apparel consolidations
    "Fabrics - Cotton, Linen, Wool, Silk, Rayon": "Fabrics",
    "Natural Fibers - Cotton": "Fabrics",
    "Natural Fibers - Linen": "Fabrics",
    "Natural Fibers - Silk": "Fabrics",
    "Natural Fibers - Wool": "Fabrics",
    "Synthetic Fibers - Rayon": "Synthetic Fabrics (Polyester, Nylon)",
    "Knitted & Woven Fabrics": "Fabrics",
    "Yarns & Fibers": "Fabrics",
    "Accessories": "Apparel Accessories",
    "Bags & Footwear": "Bags, Clutches, Wallets",
    "Bags & Luggage": "Bags, Clutches, Wallets",
    "Belts": "Belts, Ties, Caps, Hats",
    "Gloves": "Gloves & Headwear",
    "Headwear": "Belts, Ties, Caps, Hats",
    "Handkerchiefs": "Socks & Handkerchiefs",
    "Leather Goods": "Leather Goods & Accessories",
    "Casual Wear": "Men's Wear",
    "Formal Wear": "Men's Wear",
    "Party / Ethnic Wear": "Ethnic & Cultural Clothing",
    "Boys' Party & Ethnic Wear": "Kids & Baby Wear",
    "Girls' Party & Ethnic Wear": "Kids & Baby Wear",
    "Men's Party & Ethnic Wear": "Men's Wear",
    "Women's Party & Ethnic Wear": "Women's Wear",
    "Unisex Party & Ethnic Wear": "Ethnic & Cultural Clothing",
    "Baby Wear": "Kids & Baby Wear",
    "Toddler Wear": "Kids & Baby Wear",
    "Kids' Organic Clothing": "Kids & Baby Wear",
    "Men's Organic Clothing": "Men's Wear",
    "Women's Organic Clothing": "Women's Wear",
    "Organic Clothing": "Sustainable Apparel",
    "Fashion Retail POS Systems": "Fashion Services",
    "Sustainable Apparel": "Sustainable Apparel",

    # Electrical consolidations
    "Lighting Fixtures": "Lighting Fixtures & Fittings",
    "Lighting & LED Fixtures": "Lighting Fixtures & Fittings",
    "Lighting Fixtures & Bulbs": "Lighting Fixtures & Fittings",
    "Lighting Equipment": "Lighting Fixtures & Fittings",
    "Lighting Accessories": "Lighting Fixtures & Fittings",
    "Lighting Control Systems": "Automation & Control Systems",
    "Networking Devices": "Networking Equipment",
    "Security Systems": "Surveillance & Security Systems",
    "CCTV & Surveillance Systems": "Surveillance & Security Systems",
    "Access Control Systems": "Access Control Devices",
    "Time Attendance & Access Control Devices": "Access Control Devices",
    "Uninterruptible Power Supplies (UPS)": "Inverters & UPS Systems",
    "Battery Storage Systems": "Batteries, Chargers & Power Banks",
    "EV Charging Equipment": "Electric Vehicles & Charging Equipment",
    "EV Components & Batteries": "Electric Vehicles & Charging Equipment",
    "Control Panels & Switchgear": "Control Panels & PLCs",
    "Smart Building Systems & Automation": "Automation & Control Systems",
    "Embedded Systems": "PCB & Electronic Components",
    "Passive Components": "PCB & Electronic Components",
    "Capacitors, Resistors, Inductors": "PCB & Electronic Components",
    "Input Devices": "Computers, Laptops & Peripherals",
    "Computing Hardware": "Computers, Laptops & Peripherals",
    "Monitors, CPUs & Workstations": "Computers, Laptops & Peripherals",
    "Small Appliances": "Personal Care Electronics",
    "Personal Care Appliances": "Personal Care Electronics",
    "Wearable Health Technology": "Wearable Devices & Smartwatches",
    "Health & Wellness Devices": "Health Monitoring Devices",
    "Audio Accessories": "Audio Equipment",
    "Special Effects Equipment": "Sound & Lighting Systems",
    "Stage Lighting & Visuals": "Sound & Lighting Systems",
    "Video Switching Equipment": "Communication Equipment",
    "Power Distribution": "Industrial Electrical Equipment",
    "Electrical Hand Tools": "Electrical Equipment for Industrial Use",
    "AR/VR Gaming & Simulation Products": "Virtual Reality Equipment",

    # Machinery consolidations
    "3D Printing Equipment": "3D Printing Equipment for Industry",
    "Machine Tools": "Machine Tools & Accessories",
    "Pumps": "Pumps & Valves",
    "Pumps & Irrigation": "Pumps & Valves",
    "Filtration Systems": "Lubrication & Filtration Systems",
    "Filtration & Air Treatment": "Lubrication & Filtration Systems",
    "Lubrication Systems": "Lubrication & Filtration Systems",
    "Industrial Bearings & Seals": "Bearings & Seals",
    "Bearing Accessories": "Bearings & Seals",
    "HVAC Systems": "HVAC Equipment",
    "Irrigation Systems": "Irrigation Systems & Equipment",
    "Irrigation Components": "Irrigation Systems & Equipment",
    "Wood Processing Machinery": "Woodworking Machinery",
    "Metal Processing Machinery": "Metalworking Machinery",
    "Printing & Packaging Machinery": "Packaging Machinery",
    "Processing Machinery": "Packaging Machinery",
    "Material Handling": "Material Handling Equipment",
    "Raw Materials": "Chemicals & Raw Materials",
    "Industrial Equipment": "Industrial Tools",
    "Industrial Machinery": "Construction Machinery",
    "Farm Machinery & Tools": "Agricultural Machinery",
    "Greenhouse Equipment & Supplies": "Greenhouse Structures",
    "Greenhouse Supplies": "Greenhouse Structures",
    "Greenhouse Climate Control": "Greenhouse Structures",
    "Hydroponic Systems": "Hydroponic & Vertical Farming Systems",
    "Spraying Equipment": "Agricultural Machinery",
    "Planting Machinery": "Agricultural Machinery",
    "Threshing Machinery": "Agricultural Machinery",
    "Harvesting Machinery": "Agricultural Machinery",
    "Aerial Application Equipment": "Agricultural Machinery",
    "Agricultural Covers & Protection": "Agricultural Machinery",
    "Feed Preparation Machinery": "Livestock Farming Equipment",
    "Safety Footwear / Industrial Shoes": "Industrial Safety Equipment",
    "Seals": "Bearings & Seals",
    "Valves": "Pumps & Valves",
    "Cylinders": "Hydraulic & Pneumatic Equipment",
    "Accumulators": "Hydraulic & Pneumatic Equipment",
    "Actuators": "Hydraulic & Pneumatic Equipment",
    "Motion Control Components": "Automation Equipment & Robotics",
    "Robotics": "Automation Equipment & Robotics",
    "Scanning & Identification Equipment": "Testing & Measuring Instruments",
    "Testing & Inspection Equipment": "Testing & Measuring Instruments",
    "Instrumentation": "Testing & Measuring Instruments",
    "Sensors & Instrumentation": "Testing & Measuring Instruments",
    "Laboratory Tools & Instruments": "Laboratory Equipment",
    "Laboratory Glassware & Containers": "Laboratory Equipment",
    "Maintenance Kits": "Spare Parts",
    "Mould Accessories": "Casting & Forging Equipment",
    "Heat Exchangers": "Boilers & Heat Exchangers",
    "Furnace Accessories": "Industrial Ovens & Furnaces",
    "Furnace Safety Components": "Industrial Ovens & Furnaces",
    "Dryers": "Drying Equipment",
    "Mills": "Mining & Metallurgy Machinery",
    "Construction Waste Recycling Machinery": "Recycling Machinery",
    "Textile Recycling Machinery": "Recycling Machinery",
    "Scrap Metal Recycling Equipment": "Recycling Machinery",
    "Waste Management Equipment": "Recycling Machinery",
    "Eco-Friendly Dyeing Machinery": "Textile Dyeing Machinery",
    "Welding Accessories": "Welding Machines & Equipment",
    "Welding Consumables": "Welding Machines & Equipment",
    "Welding Safety Equipment": "Welding Machines & Equipment",
    "Breakroom Appliances": "Kitchen Equipment",
    "Tool Holders": "Machine Tools & Accessories",
    "Machine Accessories": "Machine Tools & Accessories",
    "Lathe Machine Accessories": "Machine Tools & Accessories",
    "Bearing Tools": "Machine Tools & Accessories",
    "Drilling Machine Accessories": "Machine Tools & Accessories",
    "Filaments & Materials": "3D Printing Equipment for Industry",
    "Manual Cleaning Tools": "Industrial Cleaning Equipment",
    "Manufacturing Equipment": "Industrial Tools",
    "Environmental Control Systems": "HVAC Equipment",
    "Material Separation Equipment": "Mining & Metallurgy Machinery",

    # Construction consolidations
    "Building Materials": "Cement, Bricks & Concrete Materials",
    "Cement & Concrete Products": "Cement, Bricks & Concrete Materials",
    "Glazing Components": "Glass & Glazing Materials",
    "Glass Processing Services": "Glass & Glazing Materials",
    "Acoustic Insulation": "Insulation Materials",
    "Machinery & Equipment": None,
    "Services": None,
    "Tools & Equipment": "Construction Tools & Hand Tools",
    "Safety Equipment": "Construction Safety Equipment",
    "Painting Tools & Equipment": "Paints, Coatings & Finishes",
    "Concrete Mixers & Batching Plants": "Construction Machinery",
    "Surveying Equipment": "Testing & Measuring Instruments",
    "Installation & Commissioning Services": "Engineering & Technical Services",
    "Instrument Calibration Services": "Engineering & Technical Services",
    "Maintenance & Repair Services": "Engineering & Technical Services",

    # Chemicals consolidations
    "Construction Chemicals": "Construction Chemicals & Adhesives",
    "Solvents & Reagents": "Acids, Solvents & Reagents",
    "Sealants": "Adhesives & Sealants",
    "Tapes & Adhesives": "Adhesives & Sealants",
    "Lubricants & Greases": "Industrial Lubricants",
    "Pigments": "Dyes & Pigments",
    "Metals": "Metal Ingots, Sheets, Rods & Wires",
    "Paper Additives": "Paper & Pulp Materials",
    "Paper Coating Chemicals": "Paper & Pulp Materials",
    "Pulp Processing Chemicals": "Paper & Pulp Materials",
    "Additives": "Plastic Additives",
    "Atmospheric Gases": "Industrial Gases",
    "Process Gases": "Industrial Gases",
    "Recycled Plastic Granules": "Plastic Raw Materials (Virgin & Recycled)",
    "Microbial Inoculants": "Agrochemicals & Biostimulants",
    "Industrial Cleaning Chemicals": "Cleaning & Sanitation Chemicals",
    "Greenhouse Films": "Packaging Raw Materials",
    "Specialty Textile Chemicals": "Textile Processing Chemicals",
    "Chemical Testing & Certification Services": "Certification Services",
    "Testing & Analysis Services": "Certification Services",
    "Certification Services": "Certification Services",

    # Office consolidations
    "Adhesives & Tapes": "Office Adhesives & Tapes",
    "Ergonomic Office Products": "Ergonomic Accessories",
    "Breakroom Consumables": "Pantry Supplies",
    "Furniture Accessories": "Office Furniture",
    "Labeling Consumables": "Filing & Organizing Supplies",
    "Networking Equipment": "Computer Accessories",

    # Services consolidations
    "Website Design & Development": "Web Design & Development",
    "Construction Chemical Services": "Engineering & Technical Services",
    "Engineering Services": "Engineering & Technical Services",
    "Equipment Services": "IT Support & Managed Services",
    "Greenhouse Services": "Environmental Consulting & Audits",
    "Interior Painting Services": "Interior Design & Space Planning",
    "Fragrances & Essential Oils": None,
    "Industrial Gases": None,
    "Sports Facility Construction Services": "Engineering & Technical Services",

    # Health consolidations
    "Aromatherapy & Wellness Products": "Essential Oils & Aromatherapy",
    "Aromatherapy Equipment": "Beauty Equipment (Salon, Spa Devices)",
    "Hair Care Tools & Accessories": "Hair Care Products",
    "Health Monitoring Accessories": "Health Monitoring Devices",
    "Bathroom Safety Equipment": "Mobility Aids",
    "Mobility Aids (Wheelchairs, Walkers)": "Mobility Aids",
    "Medical Protective Gear": "Personal Protective Equipment (PPE)",
    "Kitchen & Dining Aids": "Elderly Care Products & Solutions",
    "Telehealth Devices & Software": "Healthcare IT Solutions",
    "Software & IT Solutions": None,
    "Women's personal care products": "Women's Personal Care Products",
    "Over-the-Counter Medicines": "Over-The-Counter Medicines",

    # Home & Lifestyle consolidations
    "Bakeware": "Cookware & Bakeware",
    "Baking Tools": "Cookware & Bakeware",
    "International Cookware": "Cookware & Bakeware",
    "Cushion Covers": "Cushions & Throws",
    "Throws": "Cushions & Throws",
    "Laundry Care Equipment": "Cleaning Tools & Equipment",
    "Air Purifiers & Fans": "Cleaning Tools & Equipment",
    "Sound & Lighting Systems": "Lamps & Lighting Fixtures",
    "Sustainable Stationery": "Gift Items & Handicrafts",
    "Sustainable Bath & Body": "Home Textiles",
    "Sustainable & Eco-Friendly Products": "Gift Items & Handicrafts",
    "DJ & Studio Equipment": None,
    "Gaming Consoles & Accessories": None,
    "Event Management Services": None,

    # Sports consolidations
    "Fitness & Wellness Equipment": "Fitness Equipment (Home & Commercial)",
    "Sports Equipment (Balls, Bats, Rackets, Nets)": "Team Sports Equipment (Football, Basketball, Cricket)",
    "Consumer Electronics": None,
    "Recycling Machinery": None,

    # Tools consolidations
    "Scaffolding": "Ladders & Scaffolding",
    "Scaffolding Components": "Ladders & Scaffolding",
    "Maintenance & Repair Tools": "Hand Tools (Wrenches, Hammers, Screwdrivers)",
    "Thread Repair Kits": "Fasteners",
    "Bathroom Fittings": "Locks, Latches & Security Hardware",

    # Packaging consolidations
    "3D Prototyping Services": "3D & Custom Prototyping for Packaging",
    "Vacuum & Shrink Packaging Machinery": "Shrink Wrapping Machines",
    "Vacuum & Shrink Packaging Materials": "Vacuum & Shrink Packaging",
    "RFID Tags": "Barcode Labels & RFID Tags",
    "Food Packaging Materials": "Food Grade Packaging",
}

INVALID_SUBCATEGORY_NAMES = {
    "Machinery & Equipment", "Software & IT Solutions", "Services",
    "Raw Materials", "Industrial Gases", "Safety Equipment",
    "Packaging Machinery", "Tools & Equipment", "Services & Support",
    "Apparel & Fashion", "Agriculture & Food Products",
    "Automotive & Transport", "Chemicals & Raw Materials",
    "Construction & Infrastructure", "Electrical & Electronics",
    "Health & Personal Care", "Home & Lifestyle",
    "Office Supplies & Equipment", "Packaging & Printing",
    "Sports & Entertainment", "Tools & Hardware",
    "Medical Consumables", "Packaging Materials",
}

BUSINESS_ENTITY_KEYWORDS = [
    'manufacturer', 'manufacturers', 'exporter', 'exporters',
    'importer', 'importers', 'supplier', 'suppliers',
    'trader', 'traders', 'wholesaler', 'wholesalers',
    'distributor', 'distributors', 'dealer', 'dealers',
    'oem', 'odm', 'buying house', 'vendor', 'vendors',
    'agent', 'agents', 'broker', 'brokers', 'reseller',
]

CATEGORY_FALLBACK = {
    "Apparel & Fashion": "Apparel Accessories",
    "Agriculture & Food Products": "Agricultural Produce",
    "Machinery & Equipment": "Industrial Tools",
    "Chemicals & Raw Materials": "Industrial Chemicals",
    "Automotive & Transport": "Vehicle Spare Parts",
    "Construction & Infrastructure": "Construction Materials",
    "Electrical & Electronics": "Electronic Components",
    "Tools & Hardware": "Hand Tools (Wrenches, Hammers, Screwdrivers)",
    "Home & Lifestyle": "Home Decor Items",
    "Health & Personal Care": "Medical Consumables",
    "Packaging & Printing": "Packaging Materials",
    "Software & IT Solutions": "ERP & Business Management Software",
    "Office Supplies & Equipment": "Office Stationery",
    "Services & Support": "IT Support & Managed Services",
    "Sports & Entertainment": "Team Sports Equipment (Football, Basketball, Cricket)",
    "Energy & Power": "Renewable Energy Solutions",
}

def is_business_entity(name: str) -> bool:
    lower = name.lower()
    return any(f" {kw}" in f" {lower}" or lower.startswith(kw)
               for kw in BUSINESS_ENTITY_KEYWORDS)

def fix_row(row) -> dict:
    cat = str(row['category']).strip()
    sub = str(row['subcategory']).strip()
    prod = str(row['product_category']).strip()

    # Step 1: Canonicalize category
    cat = CANONICAL_CATEGORIES.get(cat.lower(), cat)

    # Step 2: Fix Software subcategory names to type-based names
    if cat == 'Software & IT Solutions' and sub in SOFTWARE_SUBCATEGORY_MAP:
        mapped = SOFTWARE_SUBCATEGORY_MAP[sub]
        if mapped is None:
            # This is a service — move to Services & Support
            cat = 'Services & Support'
            sub = SUBCATEGORY_REMAP_TARGET.get((sub, 'Services & Support'),
                  'Digital Marketing Services' if 'market' in sub.lower()
                  else 'Web Design & Development')
        else:
            sub = mapped

    # Step 3: Normalize subcategory name (case/consolidation)
    canonical_sub = SUBCATEGORY_NAME_CANONICAL.get(sub, sub)
    if canonical_sub is None:
        canonical_sub = CATEGORY_FALLBACK.get(cat, "General Products")
    sub = canonical_sub

    # Step 4: Move subcategory to correct category if misplaced
    if sub in SUBCATEGORY_CATEGORY_REMAP:
        new_cat = SUBCATEGORY_CATEGORY_REMAP[sub]
        new_sub = SUBCATEGORY_REMAP_TARGET.get((sub, new_cat), sub)
        cat = new_cat
        sub = new_sub

    # Step 5: Remove invalid subcategory names
    if sub in INVALID_SUBCATEGORY_NAMES:
        sub = CATEGORY_FALLBACK.get(cat, "General Products")

    # Step 6: Remove business entity subcategories
    if is_business_entity(sub):
        sub = CATEGORY_FALLBACK.get(cat, "General Products")

    return {'category': cat, 'subcategory': sub, 'product_category': prod}

def run():
    if is_completed("phase2b"):
        return

    logger.info("Starting Phase 2B — Taxonomy Corrector v3")

    input_path = os.path.join(PHASE2_OUTPUT_DIR, "merged_reorganized.csv")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Phase 2 output not found: {input_path}")

    df = pd.read_csv(input_path)
    initial = len(df)
    logger.info(f"Input rows: {initial}")

    fixed = df.apply(fix_row, axis=1, result_type='expand')
    df['category'] = fixed['category']
    df['subcategory'] = fixed['subcategory']
    df['product_category'] = fixed['product_category']
    logger.info("All fixes applied")

    # Remove exact duplicates
    before = len(df)
    df = df.drop_duplicates(subset=['category', 'subcategory', 'product_category'])
    logger.info(f"Exact duplicates removed: {before - len(df)}")

    # Resolve same product in multiple subcategories
    before = len(df)
    df['sub_len'] = df['subcategory'].str.len()
    df = df.sort_values('sub_len', ascending=False)
    df = df.drop_duplicates(subset=['category', 'product_category'], keep='first')
    df = df.drop(columns=['sub_len'])
    logger.info(f"Cross-subcategory duplicates resolved: {before - len(df)}")

    # Resolve same product across categories
    before = len(df)
    df = df.drop_duplicates(subset=['product_category'], keep='first')
    logger.info(f"Cross-category duplicates resolved: {before - len(df)}")

    df = df.dropna(subset=['category', 'subcategory', 'product_category'])
    df = df[df['product_category'].str.strip() != '']
    df = df.sort_values(['category', 'subcategory', 'product_category']).reset_index(drop=True)

    final = len(df)
    sub_count = df['subcategory'].nunique()
    logger.info(f"Phase 2B complete: {initial} → {final} rows | {sub_count} subcategories")
    logger.info(f"\nCategory distribution:\n{df['category'].value_counts().to_string()}")

    # Validation checks
    invalid_found = [s for s in df['subcategory'].unique() if s in INVALID_SUBCATEGORY_NAMES]
    if invalid_found:
        logger.warning(f"Invalid subcategory names still present: {invalid_found}")
    else:
        logger.info("✅ No invalid subcategory names")

    sw_subs = df[df['category'] == 'Software & IT Solutions']['subcategory'].value_counts()
    logger.info(f"\nSoftware & IT Solutions subcategories:\n{sw_subs.to_string()}")

    sports_count = len(df[df['category'] == 'Sports & Entertainment'])
    logger.info(f"Sports & Entertainment: {sports_count} products")

    df.to_csv(input_path, index=False, encoding='utf-8')
    corrected = os.path.join(PHASE2_OUTPUT_DIR, "corrected_taxonomy.csv")
    df.to_csv(corrected, index=False, encoding='utf-8')
    logger.info(f"Written to {input_path}")

    mark_completed("phase2b")

if __name__ == "__main__":
    run()
