FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    HF_HOME=/app/.hf \
    TRANSFORMERS_VERBOSITY=error \
    TOKENIZERS_PARALLELISM=false

# CPU-only torch: varsayilan CUDA'li surum ~2GB fazladan yer kaplar
RUN pip install --no-cache-dir \
    torch==2.5.1 --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Modeli build sirasinda indir: container basladiginda internet gerekmesin.
# Ayri layer -- kod degistiginde ~470MB tekrar indirilmez.
RUN python -c "from sentence_transformers import SentenceTransformer; \
    SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')"

COPY model.py store.py worker.py ./

CMD ["python", "worker.py"]
