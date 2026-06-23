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
# SPORTS PRODUCT KEYWORDS — reassign to Sports & Entertainment
# ============================================================
SPORTS_KEYWORDS = [
    'gym', 'fitness', 'sport', 'sports', 'exercise', 'workout',
    'yoga', 'cricket', 'football', 'basketball', 'tennis', 'badminton',
    'swimming', 'cycling', 'treadmill', 'dumbbell', 'barbell',
    'kettlebell', 'resistance band', 'boxing', 'martial arts',
    'outdoor game', 'playground', 'trampoline', 'skateboard',
    'musical instrument', 'guitar', 'drums', 'keyboard instrument',
    'trophy', 'medal', 'scoreboard', 'stadium', 'sports flooring',
    'camping', 'hiking', 'trekking', 'fishing', 'hunting',
    'billiards', 'chess', 'board game', 'playing cards',
]

# ============================================================
# BUSINESS ENTITY KEYWORDS
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
# SUBCATEGORY REMAPS
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
    "Block Making Machine Manufacturers": "Concrete & Block Making Machinery",
    "Cement Dealers & Distributors": "Cement & Concrete Products",
    "Ready Mix Concrete Suppliers": "Cement & Concrete Products",
}

CATEGORY_FALLBACK_SUBCATEGORY = {
    "Apparel & Fashion": "Apparel Accessories",
    "Agriculture & Food Products": "Agricultural Produce",
    "Machinery & Equipment": "Industrial Equipment",
    "Chemicals & Raw Materials": "Industrial Chemicals",
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
    "Sports & Entertainment": "Sports Equipment",
}

def is_business_entity(name: str) -> bool:
    lower = name.lower()
    return any(f" {kw}" in f" {lower}" or lower.startswith(kw)
               for kw in BUSINESS_ENTITY_KEYWORDS)

def is_sports_product(name: str) -> bool:
    lower = name.lower()
    return any(kw in lower for kw in SPORTS_KEYWORDS)

def fix_category(row) -> str:
    cat = str(row['category']).strip()
    canonical = CANONICAL_CATEGORIES.get(cat.lower(), cat)

    # Reassign sports products that ended up in wrong categories
    if canonical in ('Home & Lifestyle', 'Machinery & Equipment', 'Electrical & Electronics'):
        if is_sports_product(str(row['product_category'])):
            return 'Sports & Entertainment'

    return canonical

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

def collapse_single_product_subcategories(df: pd.DataFrame) -> pd.DataFrame:
    """
    Subcategories with only 1 product are too granular.
    Collapse them by assigning product to a broader sibling subcategory
    within the same category, or use the category fallback.
    """
    sub_counts = df.groupby(['category', 'subcategory']).size().reset_index(name='count')
    single_subs = sub_counts[sub_counts['count'] == 1]

    if single_subs.empty:
        return df

    logger.info(f"Collapsing {len(single_subs)} single-product subcategories")

    # For each single-product subcategory, find the most common sibling
    # subcategory in same category and reassign
    for _, row in single_subs.iterrows():
        cat = row['category']
        sub = row['subcategory']

        # Find other subcategories in same category with multiple products
        siblings = df[
            (df['category'] == cat) &
            (df['subcategory'] != sub)
        ]['subcategory'].value_counts()

        if not siblings.empty:
            # Assign to most populated sibling
            best_sibling = siblings.index[0]
            df.loc[
                (df['category'] == cat) & (df['subcategory'] == sub),
                'subcategory'
            ] = best_sibling
        else:
            # Use fallback
            fallback = CATEGORY_FALLBACK_SUBCATEGORY.get(cat, "General Products")
            df.loc[
                (df['category'] == cat) & (df['subcategory'] == sub),
                'subcategory'
            ] = fallback

    return df

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

    # Step 1 — Consolidate categories to 15 canonical
    df['category'] = df.apply(fix_category, axis=1)
    cats_after = df['category'].nunique()
    sports_count = len(df[df['category'] == 'Sports & Entertainment'])
    logger.info(f"Step 1: {cats_after} categories | Sports & Entertainment: {sports_count} products")

    # Step 2 — Fix business entity subcategories
    df['subcategory'] = df.apply(fix_subcategory, axis=1)
    logger.info("Step 2: Business entity subcategories remapped")

    # Step 3 — Clean business language from product names
    df['product_category'] = df['product_category'].apply(fix_product_category)
    logger.info("Step 3: Business language removed from product names")

    # Step 4 — Remove exact duplicates
    before = len(df)
    df = df.drop_duplicates(subset=['category', 'subcategory', 'product_category'])
    logger.info(f"Step 4: Exact duplicates removed: {before - len(df)}")

    # Step 5 — Resolve product in multiple subcategories within same category
    before = len(df)
    df['sub_len'] = df['subcategory'].str.len()
    df = df.sort_values('sub_len', ascending=False)
    df = df.drop_duplicates(subset=['category', 'product_category'], keep='first')
    df = df.drop(columns=['sub_len'])
    logger.info(f"Step 5: Cross-subcategory duplicates resolved: {before - len(df)}")

    # Step 6 — Resolve product appearing in multiple categories
    before = len(df)
    df = df.drop_duplicates(subset=['product_category'], keep='first')
    logger.info(f"Step 6: Cross-category duplicates resolved: {before - len(df)}")

    # Step 7 — Collapse single-product subcategories
    df = collapse_single_product_subcategories(df)
    logger.info("Step 7: Single-product subcategories collapsed")

    # Step 8 — Drop empty rows
    df = df.dropna(subset=['category', 'subcategory', 'product_category'])
    df = df[df['product_category'].str.strip() != '']

    # Step 9 — Sort
    df = df.sort_values(
        ['category', 'subcategory', 'product_category']
    ).reset_index(drop=True)

    final = len(df)
    sub_count = df['subcategory'].nunique()
    logger.info(f"Phase 2B complete: {initial} → {final} rows")
    logger.info(f"Final subcategory count: {sub_count}")
    logger.info(f"Category distribution:\n{df['category'].value_counts().to_string()}")

    df.to_csv(input_path, index=False, encoding='utf-8')
    logger.info(f"Clean taxonomy written to {input_path}")

    corrected_path = os.path.join(PHASE2_OUTPUT_DIR, "corrected_taxonomy.csv")
    df.to_csv(corrected_path, index=False, encoding='utf-8')
    logger.info(f"Reference copy saved to {corrected_path}")

    mark_completed("phase2b")

if __name__ == "__main__":
    run()
