import os
import pandas as pd
from common.config import PHASE2_OUTPUT_DIR
from common.logger import get_logger
from common.checkpoint import is_completed, mark_completed

logger = get_logger("phase2b")

# ============================================================
# CANONICAL 14 CATEGORIES — only these are allowed
# ============================================================
CANONICAL_CATEGORIES = {
    "apparel & fashion": "Apparel & Fashion",
    "agriculture & food products": "Agriculture & Food Products",
    "food & agriculture": "Agriculture & Food Products",
    "automotive & transport": "Automotive & Transport",
    "chemicals": "Chemicals",
    "raw materials & chemicals": "Chemicals",
    "industrial gases": "Chemicals",
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
    "tools & hardware": "Tools & Hardware",
    "textiles & fabrics": "Apparel & Fashion",
    "textile raw materials": "Apparel & Fashion",
    "sports & entertainment": "Home & Lifestyle",
    "education & training": "Services & Support",
    "education": "Services & Support",
}

# ============================================================
# BUSINESS ENTITY KEYWORDS — subcategories to reassign
# ============================================================
BUSINESS_ENTITY_KEYWORDS = [
    'manufacturer', 'manufacturers', 'exporter', 'exporters',
    'importer', 'importers', 'supplier', 'suppliers',
    'trader', 'traders', 'wholesaler', 'wholesalers',
    'distributor', 'distributors', 'dealer', 'dealers',
    'oem', 'odm', 'buying house', 'buying houses',
    'vendor', 'vendors', 'agent', 'agents',
    'broker', 'brokers', 'reseller', 'resellers',
]

# ============================================================
# EXPLICIT SUBCATEGORY REMAPS
# ============================================================
SUBCATEGORY_REMAP = {
    "Garment Manufacturers (OEM/ODM)": "Men's Wear",
    "Exporters & Buying Houses": "Apparel Accessories",
    "Wholesalers & Distributors": "Apparel Accessories",
    "Private Label Suppliers": "Apparel Accessories",
    "Fabric Traders": "Fabrics",
    "Button, Zipper, Lace, Hook Producers": "Garment Accessories & Trims",
    "Bag Manufacturers": "Bags & Luggage",
    "Bag & Footwear Manufacturers": "Bags & Footwear",
    "Footwear Manufacturers": "Footwear",
    "EVA & Rubber Footwear Manufacturers": "Footwear",
    "Canvas & Textile Goods Manufacturers": "Fabrics",
    "Leather Goods Manufacturers": "Leather Goods",
    "Leather Goods & Belt Manufacturers": "Leather Goods",
    "Private Label Bag Manufacturers": "Bags & Luggage",
    "Private Label Footwear Manufacturers": "Footwear",
    "Private Label Trim Component Suppliers": "Garment Accessories & Trims",
    "Trims And Accessories Exporters": "Garment Accessories & Trims",
    "Sampling & Prototyping Units": "Garment Accessories & Trims",
    "Jewelry Manufacturers (Costume/Fashion)": "Fashion Jewelry",
    "Embroidery Services": "Embroidery & Textile Art",
    "Eco-Friendly Dyeing Services": "Fabric Dyeing & Printing",
    "Fabric Printing & Dyeing Units": "Fabric Dyeing & Printing",
    "Fashion Design Studios": "Fashion Design",
    "Model Agencies & Styling Services": "Fashion Services",
    "Custom Design Bag & Footwear Services": "Bags & Footwear",
    "Synthetic Footwear Manufacturers": "Footwear",
    "OEM Parts Suppliers": "Spare Parts",
    "OEM Manufacturers": "Industrial Equipment",
    "OEM Tooling & Custom Tools": "Industrial Tools",
    "Oem Earthmoving Machinery Spares": "Earthmoving Equipment Parts",
    "Farm Produce Traders & Exporters": "Agricultural Produce",
    "Automobile Dealerships": "Passenger Vehicles",
    "Vehicle Dealerships": "Passenger Vehicles",
    "Commercial Vehicle Dealers & Distributors": "Commercial Vehicles",
    "Commercial Vehicle Importers & Exporters": "Commercial Vehicles",
    "Commercial Vehicle OEMs": "Commercial Vehicles",
    "OEM Vehicle Leasing Partners": "Vehicle Leasing",
    "Block Making Machine Manufacturers": "Concrete & Block Making Machinery",
    "Cement Dealers & Distributors": "Cement & Concrete Products",
    "Ready Mix Concrete Suppliers": "Cement & Concrete Products",
}

# ============================================================
# CATEGORY FALLBACK SUBCATEGORIES
# ============================================================
CATEGORY_FALLBACK_SUBCATEGORY = {
    "Apparel & Fashion": "Apparel Accessories",
    "Agriculture & Food Products": "Agricultural Produce",
    "Machinery & Equipment": "Industrial Equipment",
    "Chemicals": "Industrial Chemicals",
    "Automotive & Transport": "Auto Parts & Accessories",
    "Construction & Infrastructure": "Construction Materials",
    "Electrical & Electronics": "Electronic Components",
    "Tools & Hardware": "Hand Tools",
    "Home & Lifestyle": "Home Accessories",
    "Health & Personal Care": "Healthcare Products",
    "Packaging & Printing": "Packaging Materials",
    "Software & IT Solutions": "Business Software",
    "Office Supplies & Equipment": "Office Accessories",
    "Services & Support": "Business Services",
}

def is_business_entity(name: str) -> bool:
    lower = name.lower()
    return any(f" {kw}" in f" {lower}" or lower.startswith(kw)
               for kw in BUSINESS_ENTITY_KEYWORDS)

def fix_category(cat: str) -> str:
    return CANONICAL_CATEGORIES.get(cat.lower().strip(), cat.strip())

def fix_subcategory(row) -> str:
    sub = str(row['subcategory']).strip()
    if sub in SUBCATEGORY_REMAP:
        return SUBCATEGORY_REMAP[sub]
    if is_business_entity(sub):
        cat = str(row['category'])
        return CATEGORY_FALLBACK_SUBCATEGORY.get(cat, "General Products")
    return sub

def fix_product_category(name: str) -> str:
    replacements = [
        (' Manufacturers', ''), (' Manufacturer', ''),
        (' Exporters', ''), (' Exporter', ''),
        (' Suppliers', ''), (' Supplier', ''),
        (' Traders', ''), (' Trader', ''),
        (' Distributors', ''), (' Distributor', ''),
        (' Dealers', ''), (' Dealer', ''),
        (' Importers', ''), (' Importer', ''),
        ('OEM & ', ''), ('OEM ', ''),
        (' (OEM/ODM)', ''), ('OEM/ODM ', ''),
        ('Private Label ', ''),
        (' Wholesalers', ''), (' Wholesaler', ''),
    ]
    result = name
    for old, new in replacements:
        result = result.replace(old, new)
    return result.strip()

def run():
    if is_completed("phase2b"):
        return

    logger.info("Starting Phase 2B — Taxonomy Corrector")

    input_path = os.path.join(PHASE2_OUTPUT_DIR, "merged_reorganized.csv")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Phase 2 output not found: {input_path}")

    df = pd.read_csv(input_path)
    initial = len(df)
    logger.info(f"Input rows: {initial}")

    # Step 1 — Consolidate 32 categories → 14
    df['category'] = df['category'].apply(fix_category)
    cats_after = df['category'].nunique()
    logger.info(f"Step 1: Categories consolidated → {cats_after} unique categories")

    # Step 2 — Fix business entity subcategories
    df['subcategory'] = df.apply(fix_subcategory, axis=1)
    logger.info("Step 2: Business entity subcategories remapped")

    # Step 3 — Clean business language from product category names
    df['product_category'] = df['product_category'].apply(fix_product_category)
    logger.info("Step 3: Business language removed from product category names")

    # Step 4 — Remove exact duplicates
    before = len(df)
    df = df.drop_duplicates(subset=['category', 'subcategory', 'product_category'])
    logger.info(f"Step 4: Exact duplicates removed: {before - len(df)}")

    # Step 5 — Resolve product appearing in multiple subcategories
    # Keep most specific subcategory (longest name)
    before = len(df)
    df['sub_len'] = df['subcategory'].str.len()
    df = df.sort_values('sub_len', ascending=False)
    df = df.drop_duplicates(subset=['category', 'product_category'], keep='first')
    df = df.drop(columns=['sub_len'])
    logger.info(f"Step 5: Cross-subcategory duplicates resolved: {before - len(df)}")

    # Step 6 — Drop empty rows
    df = df.dropna(subset=['category', 'subcategory', 'product_category'])
    df = df[df['product_category'].str.strip() != '']

    # Step 7 — Sort
    df = df.sort_values(
        ['category', 'subcategory', 'product_category']
    ).reset_index(drop=True)

    final = len(df)
    logger.info(f"Phase 2B complete: {initial} → {final} rows ({initial - final} total removed)")

    # Overwrite merged_reorganized.csv — Phase 3 reads this file
    df.to_csv(input_path, index=False, encoding='utf-8')
    logger.info(f"Clean taxonomy written to {input_path}")

    # Save reference copy
    corrected_path = os.path.join(PHASE2_OUTPUT_DIR, "corrected_taxonomy.csv")
    df.to_csv(corrected_path, index=False, encoding='utf-8')
    logger.info(f"Reference copy saved to {corrected_path}")

    mark_completed("phase2b")

if __name__ == "__main__":
    run()
