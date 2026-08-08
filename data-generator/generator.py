"""RecSys 2021 Challenge sema uyumlu sentetik tweet ureteci.

Sema kaynagi: "The 2021 RecSys Challenge Dataset: Fairness is not optional",
Table 1 (https://arxiv.org/pdf/2109.08245).

Orijinal veri seti TSV formatindadir; liste tipindeki alanlar '\x01' ile
ayrilir. Bu ureteç ayni formati ve ayni kolon sirasini uretir; boylece gercek
veri sonradan bulunursa yalnizca producer'daki okuma modu degisir, hattin
geri kalani aynen calisir.

Onemli: 'tweet tokens' alani duz metin degildir. Orijinal veri setinde metin
bert-base-multilingual-cased tokenizer'i ile token ID listesine cevrilerek
yayinlanmistir. Bu ureteç de ayni tokenizer'i kullanarak GERCEK token ID'leri
uretir -- boylece downstream'deki decode adimi gercek veriyle ayni kodu calistirir.
"""

import hashlib
import random
import time

from transformers import BertTokenizerFast

import topics

# --- RecSys 2021 sema sabitleri ---------------------------------------------

LIST_SEP = "\x01"

# Table 1'deki kolon sirasi. Producer ve Spark tarafi bu sirayi paylasir.
COLUMNS = [
    "text_tokens",
    "hashtags",
    "tweet_id",
    "present_media",
    "present_links",
    "present_domains",
    "tweet_type",
    "language",
    "tweet_timestamp",
    "engaged_with_user_id",
    "engaged_with_user_follower_count",
    "engaged_with_user_following_count",
    "engaged_with_user_is_verified",
    "engaged_with_user_account_creation",
    "engaging_user_id",
    "engaging_user_follower_count",
    "engaging_user_following_count",
    "engaging_user_is_verified",
    "engaging_user_account_creation",
    "engagee_follows_engager",
]

TWEET_TYPES = ["Retweet", "Quote", "Reply", "TopLevel"]
MEDIA_TYPES = ["Photo", "Video", "Gif"]

TOKENIZER_NAME = "bert-base-multilingual-cased"

_tokenizer: BertTokenizerFast | None = None


def get_tokenizer() -> BertTokenizerFast:
    """Tokenizer'i tembel yukler (modul import'unda agir is yapmamak icin)."""
    global _tokenizer
    if _tokenizer is None:
        _tokenizer = BertTokenizerFast.from_pretrained(TOKENIZER_NAME)
    return _tokenizer


def _hashed(value: str) -> str:
    """Orijinal veri setindeki gibi hash'lenmis kimlik uretir."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:32]


class TweetGenerator:
    """RecSys 2021 semasinda TSV satirlari uretir."""

    def __init__(self, seed: int = 42, n_authors: int = 500, n_readers: int = 200):
        self.rng = random.Random(seed)
        self.tokenizer = get_tokenizer()
        self.authors = [_hashed(f"author-{i}") for i in range(n_authors)]
        self.readers = [_hashed(f"reader-{i}") for i in range(n_readers)]
        # Yazar profilleri sabit kalsin diye follower sayilarini onceden uretiyoruz
        self.author_stats = {
            a: {
                "followers": int(self.rng.lognormvariate(6.0, 2.0)),
                "following": int(self.rng.lognormvariate(5.0, 1.5)),
                "verified": self.rng.random() < 0.05,
                "created": int(time.time()) - self.rng.randint(86400 * 30, 86400 * 3650),
            }
            for a in self.authors
        }
        self.reader_stats = {
            r: {
                "followers": int(self.rng.lognormvariate(5.0, 1.8)),
                "following": int(self.rng.lognormvariate(5.5, 1.2)),
                "verified": self.rng.random() < 0.02,
                "created": int(time.time()) - self.rng.randint(86400 * 30, 86400 * 3650),
            }
            for r in self.readers
        }
        self._counter = 0

    def generate(self) -> tuple[str, str, str]:
        """Tek bir kayit uretir.

        Donen deger: (tweet_id, tsv_satiri, konu)
        Konu yalnizca degerlendirme icindir; TSV'ye yazilmaz -- gercek veri
        setinde boyle bir alan yoktur.
        """
        rng = self.rng
        topic, lang, text, tags = topics.pick_text(rng)

        # Ayni metnin tekrar etmesi dogal; ama tweet_id benzersiz olmali.
        # Dedup testini beslemek icin kasitli olarak bazen ayni id'yi tekrar
        # uretiyoruz (asagida generate_batch icinde).
        self._counter += 1
        tweet_id = _hashed(f"tweet-{self._counter}-{rng.random()}")

        # GERCEK mBERT token id'leri -- gercek veri setiyle ayni kodlama
        token_ids = self.tokenizer.encode(text, add_special_tokens=True)

        author = rng.choice(self.authors)
        reader = rng.choice(self.readers)
        a = self.author_stats[author]
        r = self.reader_stats[reader]

        media = []
        if rng.random() < 0.25:
            media = [rng.choice(MEDIA_TYPES)]

        links, domains = [], []
        if rng.random() < 0.15:
            links = [_hashed(f"link-{rng.random()}")]
            domains = [_hashed(rng.choice(["twitter.com", "youtube.com", "github.com"]))]

        now = int(time.time())
        # Tweet zamani son 48 saat icinde -- recency skorunun anlamli olmasi icin
        tweet_ts = now - rng.randint(0, 48 * 3600)

        row = [
            LIST_SEP.join(str(t) for t in token_ids),       # text_tokens
            LIST_SEP.join(tags),                            # hashtags
            tweet_id,                                       # tweet_id
            LIST_SEP.join(media),                           # present_media
            LIST_SEP.join(links),                           # present_links
            LIST_SEP.join(domains),                         # present_domains
            rng.choice(TWEET_TYPES),                        # tweet_type
            lang,                                           # language
            str(tweet_ts),                                  # tweet_timestamp
            author,                                         # engaged_with_user_id
            str(a["followers"]),
            str(a["following"]),
            str(a["verified"]).lower(),
            str(a["created"]),
            reader,                                         # engaging_user_id
            str(r["followers"]),
            str(r["following"]),
            str(r["verified"]).lower(),
            str(r["created"]),
            str(rng.random() < 0.6).lower(),                # engagee_follows_engager
        ]

        assert len(row) == len(COLUMNS), (
            f"kolon sayisi uyusmuyor: {len(row)} != {len(COLUMNS)}"
        )
        return tweet_id, "\t".join(row), topic

    def generate_with_duplicates(self, duplicate_rate: float = 0.05):
        """Uretim akisi; belirli oranda kasitli tekrar kaydi icerir.

        Spark tarafindaki dedup adiminin gercekten bir sey yaptigini
        gosterebilmek icin tekrar kayitlar uretiyoruz (rapor §3.3).
        """
        recent: list[tuple[str, str, str]] = []
        while True:
            if recent and self.rng.random() < duplicate_rate:
                yield self.rng.choice(recent)
                continue

            record = self.generate()
            recent.append(record)
            if len(recent) > 50:
                recent.pop(0)
            yield record


if __name__ == "__main__":
    # Hizli gorsel kontrol: birkac satir uret ve decode edilebildigini dogrula
    gen = TweetGenerator(seed=1)
    tok = gen.tokenizer
    for _ in range(3):
        tid, row, topic = gen.generate()
        token_ids = [int(x) for x in row.split("\t")[0].split(LIST_SEP)]
        print(f"[{topic}] {tid[:12]}...")
        print(f"  tokens : {token_ids[:12]}...")
        print(f"  decoded: {tok.decode(token_ids, skip_special_tokens=True)}")
        print()
