# B2B Taxonomy Pipeline

Fully automated taxonomy reorganization engine for B2B product categories.

## Architecture

exit
cat > README.md << 'EOF'
# B2B Taxonomy Pipeline

Fully automated taxonomy reorganization engine for B2B product categories.

## Architecture
Input CSV

↓

Phase 1  → Batch Generator

Phase 2  → Qwen Taxonomy Architect (LLM)

Phase 2B → Rule-Based Corrector

Phase 3  → BGE Embeddings + FAISS

Phase 4  → Qwen Synonym Merge (LLM)

Phase 5  → Validator

↓

output/phase5/final_taxonomy.csv

## Stack
- LLM: Qwen3.5 9B MLX via Ollama (local)
- Embeddings: BAAI/bge-small-en-v1.5
- Vector Search: FAISS
- Runtime: Python 3.14

## Setup

```bash
git clone https://github.com/deepakPEP/pep-category-taxonomy.git
cd pep-category-taxonomy
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Ollama model name
# Place your CSV in input/
python run_pipeline.py
```

## Input Format
Category,Subcategory,Product Category

Apparel & Fashion,Men's Wear,Men's Formal Shirts

Tab and comma separated both supported.

## Output

- `output/phase5/final_taxonomy.csv` — clean taxonomy
- `output/metrics/metrics.json` — run statistics
- `output/logs/taxonomy.log` — full log
EOFq!
cat > README.md << 'EOF'
# B2B Taxonomy Pipeline

Fully automated taxonomy reorganization engine for B2B product categories.

## Architecture
Input CSV

↓

Phase 1  → Batch Generator

Phase 2  → Qwen Taxonomy Architect (LLM)

Phase 2B → Rule-Based Corrector

Phase 3  → BGE Embeddings + FAISS

Phase 4  → Qwen Synonym Merge (LLM)

Phase 5  → Validator

↓

output/phase5/final_taxonomy.csv

## Stack
- LLM: Qwen3.5 9B MLX via Ollama (local)
- Embeddings: BAAI/bge-small-en-v1.5
- Vector Search: FAISS
- Runtime: Python 3.14

## Setup

```bash
git clone https://github.com/deepakPEP/pep-category-taxonomy.git
cd pep-category-taxonomy
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Ollama model name
# Place your CSV in input/
python run_pipeline.py
```

## Input Format
Category,Subcategory,Product Category

Apparel & Fashion,Men's Wear,Men's Formal Shirts

Tab and comma separated both supported.

## Output

- `output/phase5/final_taxonomy.csv` — clean taxonomy
- `output/metrics/metrics.json` — run statistics
- `output/logs/taxonomy.log` — full log
