"""Embedding modeli yukleme ve vektorlestirme.

Model modul seviyesinde bir kez yuklenir. Her mesajda yeniden yuklemek
felaket olurdu (~2sn/mesaj yerine ~5ms/mesaj).

Secilen model: paraphrase-multilingual-MiniLM-L12-v2
  - 384 boyut, cok dilli (50+ dil)
  - RecSys 2021 verisi 104 dil iceriyor -> cok dilli model zorunlu
  - Yerel calisir, API anahtari gerekmez
"""

import logging
import os
import threading

import numpy as np
from sentence_transformers import SentenceTransformer

log = logging.getLogger(__name__)

MODEL_NAME = os.getenv("MODEL_NAME", "paraphrase-multilingual-MiniLM-L12-v2")
VECTOR_SIZE = 384

_model: SentenceTransformer | None = None
_lock = threading.Lock()


def get_model() -> SentenceTransformer:
    """Modeli tembel + thread-safe yukler.

    HTTP servisi ve consumer dongusu ayni modeli paylasir; iki thread'in
    ayni anda yuklemeye calismasini engelliyoruz.
    """
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                log.info("model yukleniyor: %s", MODEL_NAME)
                _model = SentenceTransformer(MODEL_NAME)
                dim = _model.get_sentence_embedding_dimension()
                if dim != VECTOR_SIZE:
                    raise RuntimeError(
                        f"model boyutu beklenenden farkli: {dim} != {VECTOR_SIZE}"
                    )
                log.info("model hazir (boyut=%d)", dim)
    return _model


def embed(texts: list[str]) -> np.ndarray:
    """Metin listesini vektorlestirir.

    Batch halinde encode ediyoruz -- tek tek cagirmaktan ~10x hizli.
    Vektorler normalize edilir; boylece Qdrant'taki cosine mesafesi
    dogrudan nokta carpimina denk gelir ve kullanici profili icin
    ortalama almak dogru davranir.
    """
    if not texts:
        return np.zeros((0, VECTOR_SIZE), dtype=np.float32)

    vectors = get_model().encode(
        texts,
        batch_size=32,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return vectors.astype(np.float32)


def embed_one(text: str) -> np.ndarray:
    """Tek metni vektorlestirir."""
    return embed([text])[0]


def average_vector(vectors: np.ndarray) -> np.ndarray:
    """Vektorlerin ortalamasini alip normalize eder.

    Kullanici profil vektoru boyle olusur (rapor §4 adim 7): ilgi
    alanlarinin vektorlerinin ortalamasi. Normalize etmezsek ilgi alani
    sayisi arttikca vektorun boyu degisir ve cosine skorlari kayar.
    """
    if len(vectors) == 0:
        raise ValueError("bos vektor listesi")

    mean = vectors.mean(axis=0)
    norm = np.linalg.norm(mean)
    if norm < 1e-9:
        # Birbirini goturen vektorler -- nadir ama mumkun
        raise ValueError("ortalama vektor sifira cok yakin")
    return (mean / norm).astype(np.float32)
