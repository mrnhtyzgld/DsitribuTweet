FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    HF_HOME=/app/.hf \
    TRANSFORMERS_VERBOSITY=error

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Tokenizer'i build sirasinda indir: container basladiginda internet gerekmesin.
# Ayri bir layer -- kod degistiginde yeniden indirilmez.
RUN python -c "from transformers import BertTokenizerFast; \
    BertTokenizerFast.from_pretrained('bert-base-multilingual-cased')"

COPY schema.py topics.py generator.py brightdata.py producer.py ./

CMD ["python", "producer.py"]
