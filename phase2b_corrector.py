import os
import pandas as pd
from common.config import PHASE2_OUTPUT_DIR
from common.logger import get_logger
from common.checkpoint import is_completed, mark_completed

logger = get_logger("phase2b")

# ============================================================
# CANONICAL 15 CATEGORIES
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
}

# ============================================================
# P0 FIX: SUBCATEGORY → CORRECT CATEGORY REMAP
# Every subcategory that belongs in a different category
# ============================================================
SUBCATEGORY_CATEGORY_REMAP = {
    # Agriculture wrongly placed subcategories
    "Leather & Hides": "Apparel & Fashion",
    "Textile Raw Materials": "Apparel & Fashion",
    "Recycled Apparel": "Apparel & Fashion",
    "Fashion Design Services": "Services & Support",
    "Timber & Logs": "Construction & Infrastructure",
    "Wood & Wood Products": "Construction & Infrastructure",
    "Processed Wood": "Construction & Infrastructure",
    "Biodegradable & Sustainable Raw Materials": "Chemicals & Raw Materials",

    # Electrical & Electronics wrongly placed subcategories
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

    # Home & Lifestyle — sports products wrongly placed
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

    # Machinery wrongly placed subcategories
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

    # Chemicals wrongly placed subcategories
    "Food Additives & Preservatives": "Agriculture & Food Products",
    "Food Additives & Ingredients": "Agriculture & Food Products",
    "Agrochemicals": "Agriculture & Food Products",
    "Agrochemicals & Biostimulants": "Agriculture & Food Products",
    "Pesticides & Crop Protection": "Agriculture & Food Products",
    "Organic Pesticides": "Agriculture & Food Products",
    "Fertilizers & Soil Conditioners": "Agriculture & Food Products",

    # Construction wrongly placed subcategories
    "Workshop Equipment": "Tools & Hardware",
    "Tool Room Equipment": "Tools & Hardware",

    # Sports wrongly placed subcategories
    "Recycling Machinery": "Machinery & Equipment",
    "Consumer Electronics": "Electrical & Electronics",

    # Software wrongly placed subcategories
    "Barcode Labels & RFID Tags": "Packaging & Printing",
    "Control Panels & PLCs": "Electrical & Electronics",
    "Cold Chain Logistics & Storage": "Agriculture & Food Products",

    # Health wrongly placed subcategories
    "Restroom Furniture": "Office Supplies & Equipment",

    # Automotive duplicates
    "Vehicle Insurance And Financing": "Automotive & Transport",
    "Fleet Management Solutions": "Automotive & Transport",
    "Retreaded Tyres": "Automotive & Transport",
    "Steering Components": "Automotive & Transport",
    "Suspension Components": "Automotive & Transport",
    "Lighting & Signaling Devices": "Automotive & Transport",
}

# ============================================================
# P1 FIX: SUBCATEGORY NAME CANONICAL MAPPING
# Resolve case duplicates and naming inconsistencies
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
    "Semiconductors & ICs": "Semiconductors & ICs",
    "Security Systems": "Surveillance & Security Systems",
    "CCTV & Surveillance Systems": "Surveillance & Security Systems",
    "Access Control Systems": "Access Control Devices",
    "Time Attendance & Access Control Devices": "Access Control Devices",
    "Generators & Alternators": "Generators & Alternators",
    "Inverters & UPS Systems": "Inverters & UPS Systems",
    "Uninterruptible Power Supplies (UPS)": "Inverters & UPS Systems",
    "Battery Storage Systems": "Batteries, Chargers & Power Banks",
    "EV Charging Equipment": "Electric Vehicles & Charging Equipment",
    "EV Components & Batteries": "Electric Vehicles & Charging Equipment",
    "Control Panels & Switchgear": "Control Panels & PLCs",
    "Automation & Control Systems": "Automation & Control Systems",
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
    "Recycling & Waste Processing Materials": "PCB & Electronic Components",

    # Machinery consolidations
    "3D Printing Equipment": "3D Printing Equipment for Industry",
    "Cnc Machines": "CNC Machines",
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
    "Pumps & Irrigation": "Irrigation Systems & Equipment",
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
    "Post-Harvest Processing": "Food Processing Machinery",
    "Pre-Processing & Cleaning Equipment": "Food Processing Machinery",
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
    "Workbenches & Workshop Tools": "Workbenches & Workshop Tools",
    "Stage, Set & Truss Equipment": "Sports & Entertainment",
    "Filaments & Materials": "3D Printing Equipment for Industry",
    "Manual Cleaning Tools": "Industrial Cleaning Equipment",
    "Manufacturing Equipment": "Industrial Tools",
    "Environmental Control Systems": "HVAC Equipment",
    "Material Separation Equipment": "Mining & Metallurgy Machinery",
    "Casting & Forging Equipment": "Casting & Forging Equipment",

    # Construction consolidations
    "Building Materials": "Cement, Bricks & Concrete Materials",
    "Cement & Concrete Products": "Cement, Bricks & Concrete Materials",
    "Glazing Components": "Glass & Glazing Materials",
    "Glass Processing Services": "Glass & Glazing Materials",
    "Acoustic Insulation": "Insulation Materials",
    "Lighting Fixtures & Fittings": "Lighting Fixtures & Fittings",
    "Machinery & Equipment": None,  # Invalid subcategory name — reassign products
    "Services": None,  # Invalid subcategory name — reassign products
    "Tools & Equipment": "Construction Tools & Hand Tools",
    "Safety Equipment": "Construction Safety Equipment",
    "Painting Tools & Equipment": "Paints, Coatings & Finishes",
    "Concrete Mixers & Batching Plants": "Construction Machinery",
    "Surveying Equipment": "Machinery & Equipment",
    "HVAC Systems": "HVAC Equipment",
    "Installation & Commissioning Services": "Engineering & Technical Services",
    "Instrument Calibration Services": "Engineering & Technical Services",
    "Glass Processing Services": "Glass & Glazing Materials",
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
    "Monitors, CPUs & Workstations": "Computer Accessories",
    "Packaging Machinery": None,  # Invalid in Office — reassign products
    "Machinery & Equipment": None,  # Invalid in Office — reassign products
    "Office Phones & Intercom Systems": "Office Supplies & Equipment",

    # Packaging consolidations
    "3D Prototyping Services": "3D & Custom Prototyping for Packaging",
    "Vacuum & Shrink Packaging Machinery": "Shrink Wrapping Machines",
    "Vacuum & Shrink Packaging Materials": "Vacuum & Shrink Packaging",
    "RFID Tags": "Barcode Labels & RFID Tags",
    "Raw Materials": None,  # Invalid — reassign to Chemicals & Raw Materials
    "Machinery & Equipment": None,  # Invalid — reassign to Machinery & Equipment
    "Food Packaging Materials": "Food Grade Packaging",

    # Services consolidations
    "Website Design & Development": "Web Design & Development",
    "Construction Chemical Services": "Engineering & Technical Services",
    "Engineering Services": "Engineering & Technical Services",
    "Equipment Services": "IT Support & Managed Services",
    "Greenhouse Services": "Environmental Consulting & Audits",
    "Interior Painting Services": "Interior Design & Space Planning",
    "Fragrances & Essential Oils": None,  # Not a service — reassign to Chemicals
    "Industrial Gases": None,  # Not a service — reassign to Chemicals
    "Sports Facility Construction Services": "Engineering & Technical Services",

    # Software consolidations
    "AR/VR Development Services": "AR/VR Development Software",
    "AR/VR Development Tools": "AR/VR Development Software",
    "Simulation Software": "Simulation & Modeling Software",
    "Industrial Software": "Industrial Automation Software",
    "Industrial Control Systems": "Industrial Automation Software",
    "Digital Imaging Services": "Digital Marketing Services",
    "Digital Health & Wellness Software": "Mental Health & Wellness Software",
    "STEM Software": "Educational Software",
    "Educational Games": "Educational Software",
    "Software & IT Solutions": None,  # Invalid subcategory name
    "Fashion Retail POS Systems": "Retail Point of Sale (POS) Software",
    "Healthcare IT Solutions": "Healthcare IT Solutions",
    "Cold Chain Logistics & Storage": None,  # Not software — reassign
    "Garment Accessories & Trims": None,  # Not software — reassign
    "Barcode Labels & RFID Tags": None,  # Not software — reassign
    "Control Panels & PLCs": None,  # Not software — reassign

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
    "Software & IT Solutions": None,  # Invalid subcategory name
    "Women's personal care products": "Women's Personal Care Products",
    "Over-the-Counter Medicines": "Over-The-Counter Medicines",

    # Home & Lifestyle consolidations
    "Bakeware": "Cookware & Bakeware",
    "Baking Tools": "Cookware & Bakeware",
    "International Cookware": "Cookware & Bakeware",
    "Cushion Covers": "Cushions & Throws",
    "Throws": "Cushions & Throws",
    "Bath Linens And Towels": "Bath Linens & Towels",
    "Mattresses And Mattress Toppers": "Mattresses & Mattress Toppers",
    "Artificial Plants And Flowers": "Artificial Plants & Flowers",
    "Laundry Care Equipment": "Cleaning Tools & Equipment",
    "Air Purifiers & Fans": "Cleaning Tools & Equipment",
    "Smart Home Devices": "Smart Home Devices",
    "Sound & Lighting Systems": "Lamps & Lighting Fixtures",
    "Sustainable Stationery": "Gift Items & Handicrafts",
    "Sustainable Bath & Body": "Home Textiles",
    "Sustainable & Eco-Friendly Products": "Gift Items & Handicrafts",
    "Services": None,  # Invalid subcategory name
    "DJ & Studio Equipment": None,  # Goes to Sports & Entertainment
    "Gaming Consoles & Accessories": None,  # Goes to Electrical & Electronics
    "Event Management Services": None,  # Goes to Services & Support

    # Sports & Entertainment consolidations
    "Fitness & Wellness Equipment": "Fitness Equipment (Home & Commercial)",
    "Sports Equipment (Balls, Bats, Rackets, Nets)": "Team Sports Equipment (Football, Basketball, Cricket)",
    "Consumer Electronics": None,  # Goes to Electrical & Electronics
    "Recycling Machinery": None,  # Goes to Machinery & Equipment
    "Children's Play Equipment & Toys": "Board Games & Puzzles",

    # Tools & Hardware consolidations
    "Scaffolding": "Ladders & Scaffolding",
    "Scaffolding Components": "Ladders & Scaffolding",
    "Maintenance & Repair Tools": "Hand Tools (Wrenches, Hammers, Screwdrivers)",
    "Machinery & Equipment": None,  # Invalid subcategory name
    "Bathroom Fittings": "Locks, Latches & Security Hardware",
    "Gardening Tools": "Gardening Tools",
    "Thread Repair Kits": "Fasteners",
    "Hydraulic Tools": "Hydraulic Tools",
}

# ============================================================
# CATEGORY FALLBACK SUBCATEGORIES
# When a subcategory is remapped to a new category,
# use this as the target subcategory
# ============================================================
SUBCATEGORY_REMAP_TARGET = {
    # What subcategory to use when moving to a new category
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
    ("Barcode Labels & RFID Tags", "Packaging & Printing"): "Barcode Labels & RFID Tags",
    ("Control Panels & PLCs", "Electrical & Electronics"): "Control Panels & PLCs",
    ("Cold Chain Logistics & Storage", "Agriculture & Food Products"): "Cold Chain Logistics & Storage",
    ("Restroom Furniture", "Office Supplies & Equipment"): "Office Furniture",
    ("Fragrances & Essential Oils", "Chemicals & Raw Materials"): "Fragrances & Essential Oils",
    ("Industrial Gases", "Chemicals & Raw Materials"): "Industrial Gases",
}

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
    "Software & IT Solutions": "Business Management Software",
    "Office Supplies & Equipment": "Office Stationery",
    "Services & Support": "IT Support & Managed Services",
    "Sports & Entertainment": "Sports Equipment (Balls, Bats, Rackets, Nets)",
}

INVALID_SUBCATEGORY_NAMES = {
    "Machinery & Equipment",
    "Software & IT Solutions",
    "Services",
    "Raw Materials",
    "Industrial Gases",
    "Safety Equipment",
    "Packaging Machinery",
    "Tools & Equipment",
    "Services & Support",
    "Apparel & Fashion",
    "Agriculture & Food Products",
    "Automotive & Transport",
    "Chemicals & Raw Materials",
    "Construction & Infrastructure",
    "Electrical & Electronics",
    "Health & Personal Care",
    "Home & Lifestyle",
    "Office Supplies & Equipment",
    "Packaging & Printing",
    "Sports & Entertainment",
    "Tools & Hardware",
}

BUSINESS_ENTITY_KEYWORDS = [
    'manufacturer', 'manufacturers', 'exporter', 'exporters',
    'importer', 'importers', 'supplier', 'suppliers',
    'trader', 'traders', 'wholesaler', 'wholesalers',
    'distributor', 'distributors', 'dealer', 'dealers',
    'oem', 'odm', 'buying house', 'buying houses',
    'vendor', 'vendors', 'agent', 'agents',
    'broker', 'brokers', 'reseller', 'resellers',
]

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

    # Step 2: Normalize subcategory name (case duplicates, consolidation)
    canonical_sub = SUBCATEGORY_NAME_CANONICAL.get(sub, sub)
    if canonical_sub is None:
        canonical_sub = CATEGORY_FALLBACK.get(cat, "General Products")
    sub = canonical_sub

    # Step 3: Move subcategory to correct category if misplaced
    if sub in SUBCATEGORY_CATEGORY_REMAP:
        new_cat = SUBCATEGORY_CATEGORY_REMAP[sub]
        new_sub = SUBCATEGORY_REMAP_TARGET.get((sub, new_cat), sub)
        cat = new_cat
        sub = new_sub

    # Step 4: Remove invalid subcategory names (category names used as subcategories)
    if sub in INVALID_SUBCATEGORY_NAMES:
        sub = CATEGORY_FALLBACK.get(cat, "General Products")

    # Step 5: Remove business entities as subcategories
    if is_business_entity(sub):
        sub = CATEGORY_FALLBACK.get(cat, "General Products")

    return {'category': cat, 'subcategory': sub, 'product_category': prod}

def run():
    if is_completed("phase2b"):
        return

    logger.info("Starting Phase 2B — Taxonomy Corrector v2")

    input_path = os.path.join(PHASE2_OUTPUT_DIR, "merged_reorganized.csv")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Phase 2 output not found: {input_path}")

    df = pd.read_csv(input_path)
    initial = len(df)
    logger.info(f"Input rows: {initial}")

    # Apply all fixes row by row
    fixed_rows = df.apply(fix_row, axis=1, result_type='expand')
    df['category'] = fixed_rows['category']
    df['subcategory'] = fixed_rows['subcategory']
    df['product_category'] = fixed_rows['product_category']
    logger.info("All category, subcategory, and placement fixes applied")

    # Remove exact duplicates
    before = len(df)
    df = df.drop_duplicates(subset=['category', 'subcategory', 'product_category'])
    logger.info(f"Exact duplicates removed: {before - len(df)}")

    # Resolve same product in multiple subcategories within same category
    before = len(df)
    df['sub_len'] = df['subcategory'].str.len()
    df = df.sort_values('sub_len', ascending=False)
    df = df.drop_duplicates(subset=['category', 'product_category'], keep='first')
    df = df.drop(columns=['sub_len'])
    logger.info(f"Cross-subcategory duplicates resolved: {before - len(df)}")

    # Resolve same product across multiple categories
    before = len(df)
    df = df.drop_duplicates(subset=['product_category'], keep='first')
    logger.info(f"Cross-category duplicates resolved: {before - len(df)}")

    # Drop empty rows
    df = df.dropna(subset=['category', 'subcategory', 'product_category'])
    df = df[df['product_category'].str.strip() != '']

    # Sort
    df = df.sort_values(
        ['category', 'subcategory', 'product_category']
    ).reset_index(drop=True)

    final = len(df)
    sub_count = df['subcategory'].nunique()
    logger.info(f"Phase 2B complete: {initial} → {final} rows")
    logger.info(f"Subcategories: {sub_count}")
    logger.info(f"\nCategory distribution:\n{df['category'].value_counts().to_string()}")

    # Verify no invalid subcategory names remain
    invalid_found = [s for s in df['subcategory'].unique() if s in INVALID_SUBCATEGORY_NAMES]
    if invalid_found:
        logger.warning(f"Invalid subcategory names still present: {invalid_found}")
    else:
        logger.info("✅ No invalid subcategory names found")

    # Verify no cross-category subcategory duplicates
    sub_cats = df.groupby('subcategory')['category'].nunique()
    dup_subs = sub_cats[sub_cats > 1]
    if not dup_subs.empty:
        logger.warning(f"Subcategories still in multiple categories: {len(dup_subs)}")
        for sub in list(dup_subs.index)[:10]:
            cats = df[df['subcategory'] == sub]['category'].unique()
            logger.warning(f"  '{sub}' → {list(cats)}")
    else:
        logger.info("✅ No cross-category subcategory duplicates found")

    # Sports & Entertainment check
    sports_count = len(df[df['category'] == 'Sports & Entertainment'])
    logger.info(f"Sports & Entertainment: {sports_count} products")

    df.to_csv(input_path, index=False, encoding='utf-8')
    logger.info(f"Written to {input_path}")

    corrected_path = os.path.join(PHASE2_OUTPUT_DIR, "corrected_taxonomy.csv")
    df.to_csv(corrected_path, index=False, encoding='utf-8')

    mark_completed("phase2b")

if __name__ == "__main__":
    run()
