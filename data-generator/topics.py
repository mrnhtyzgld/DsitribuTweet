"""Konu havuzu ve cok dilli tweet sablonlari.

Her uretilen tweet bir konuya aittir. Bu, oneri sisteminin dogru calistigini
gozle dogrulanabilir kilar: "GPU programlama" ilgi alani giren bir kullaniciya
donen feed'de teknoloji tweetlerinin agirlikta olmasi beklenir.

Konu etiketi payload'a yazilir ama embedding'e girmez -- sadece degerlendirme
icin tutulur.
"""

import random

# RecSys 2021 veri setindeki language alani hash'lenmis kimliklerdir.
# Burada okunabilirlik icin ISO kodlari kullaniyoruz.
LANGUAGES = ["tr", "en", "de", "fr"]

# konu -> dil -> cumle parcalari
TOPICS = {
    "teknoloji": {
        "tr": [
            "Spark Structured Streaming ile gercek zamanli veri isleme deniyorum",
            "Kubernetes uzerinde mikroservis dagitimi beklediginden daha kolaymis",
            "GPU programlama ve CUDA kernel optimizasyonu uzerine calisiyorum",
            "Kafka partition sayisini artirinca throughput ciddi sekilde yukseldi",
            "Scala ile fonksiyonel programlama ogrenmek zaman aliyor ama degiyor",
            "Vektor veritabanlari benzerlik aramasini inanilmaz hizlandiriyor",
            "Docker Compose ile tum stack'i tek komutla ayaga kaldirdim",
            "Dagitik sistemlerde consensus algoritmalari hep kafa karistirici",
            "Tip guvenligi sayesinde bir suru hatayi derleme aninda yakaladim",
            "Veritabani indeksini duzeltince sorgu suresi yuzde doksan dustu",
            "Kod incelemesi kultur meselesi arac meselesi degil",
            "Onbellek gecersizlestirme gercekten en zor problemlerden biri",
            "Test yazmak yavaslatir sanirdim tam tersi cikti",
            "Mikroservise gecmeden once monolitin sinirlarini anlamak sart",
        ],
        "en": [
            "Real time stream processing with Spark is finally clicking for me",
            "Deployed my first Kubernetes cluster today and nothing caught fire",
            "CUDA kernel optimization gave us a 4x speedup on inference",
            "Kafka consumer groups make horizontal scaling almost trivial",
            "Learning functional programming in Scala has changed how I code",
            "Vector databases are a game changer for semantic search",
            "Spent the whole day debugging a race condition in distributed code",
            "Embedding models keep getting smaller and faster every month",
            "One database index fixed a query that took ten seconds",
            "Static typing caught a whole class of bugs before runtime",
            "Cache invalidation really is one of the hard problems",
            "Writing tests felt slow until it started saving me hours",
            "Code review is a culture problem not a tooling problem",
            "Understand your monolith boundaries before splitting services",
        ],
        "de": [
            "Verteilte Systeme sind faszinierend und frustrierend zugleich",
            "Heute meinen ersten Kafka Consumer in Produktion gebracht",
            "Maschinelles Lernen auf der GPU ist deutlich schneller",
        ],
        "fr": [
            "Le traitement de donnees en temps reel avec Spark est puissant",
            "Les bases de donnees vectorielles changent la recherche semantique",
            "J apprends la programmation fonctionnelle avec Scala",
        ],
    },
    "spor": {
        "tr": [
            "Dun geceki mac son dakikada golle bitti inanilmazdi",
            "Basketbolda savunma organizasyonu her seyden onemli",
            "Maraton antrenmanina basladim ilk hafta bacaklarim tutmuyor",
            "Transfer sezonu basladi kulubumuz yine hareketsiz",
            "Yuzmeye baslamak eklemlerim icin en iyi karar oldu",
            "Hakem kararlari mac sonucunu degistirdi diye dusunmuyorum",
            "Antrenman sonrasi toparlanma en az antrenman kadar onemli",
            "Bisikletle ise gitmek hem ucuz hem keyifli cikti",
        ],
        "en": [
            "What a comeback in the second half nobody saw that coming",
            "Marathon training week three and my legs have opinions",
            "The defensive rotation in that game was absolutely perfect",
            "Transfer window rumors are getting completely out of hand",
            "Swimming turned out to be the best call for my joints",
            "Recovery matters as much as the training itself",
            "Cycling to work is cheaper and more fun than I expected",
            "I do not think the referee decisions changed that result",
        ],
        "de": [
            "Das Spiel gestern Abend war einfach unglaublich spannend",
            "Marathontraining ist harter als ich erwartet hatte",
        ],
        "fr": [
            "Quel match hier soir vraiment incroyable jusqu au bout",
            "Je commence l entrainement pour le marathon cette semaine",
        ],
    },
    "muzik": {
        "tr": [
            "Yeni albumu bastan sona dinledim ve prodüksiyon muhtesem",
            "Gitar calmayi ogreniyorum parmak uclarim aci icinde",
            "Konser biletleri bes dakikada tukendi yine kacirdik",
            "Vinil koleksiyonum kontrolden cikmaya basladi",
        ],
        "en": [
            "This new album is a masterpiece from start to finish",
            "Learning guitar as an adult is humbling in the best way",
            "Concert tickets sold out in four minutes what is happening",
            "My vinyl collection has officially outgrown the shelf",
        ],
        "de": [
            "Das neue Album ist von vorne bis hinten grossartig",
            "Gitarre lernen macht mehr Spass als gedacht",
        ],
        "fr": [
            "Ce nouvel album est une reussite du debut a la fin",
            "J apprends la guitare et mes doigts souffrent beaucoup",
        ],
    },
    "yemek": {
        "tr": [
            "Ekmek mayasini besledim ve nihayet duzgun kabardi",
            "Bu tarifte tereyagi yerine zeytinyagi kullanmak daha iyi sonuc verdi",
            "Mangal keyfi icin hava nihayet uygun hale geldi",
            "Kahve demleme yontemini degistirdim tat farki inanilmaz",
            "Firinda sebze kavurmak icin dusuk isi ve uzun sure gerekiyor",
            "Baharat dolabimi duzenledim yarisinin tarihi gecmis",
            "Evde makarna yapmak sandigimdan cok daha kolay cikti",
            "Corba icin ev yapimi et suyu kullanmak her seyi degistiriyor",
            "Kek tarifinde yumurtalarin oda sicakliginda olmasi onemliymis",
            "Sogani karamelize etmek yirmi dakika degil kirk dakika suruyor",
        ],
        "en": [
            "My sourdough starter finally produced a proper rise today",
            "Swapping butter for olive oil made this recipe so much better",
            "Slow roasted the vegetables for two hours and it was worth it",
            "Changed my coffee brewing method and the difference is wild",
            "Homemade pasta turned out far easier than I expected",
            "Using real stock instead of cubes transforms any soup",
            "Room temperature eggs actually matter in baking apparently",
            "Caramelizing onions takes forty minutes not twenty",
            "Reorganized my spice rack and half of it had expired",
            "Toasting the spices before grinding makes a huge difference",
        ],
        "de": [
            "Mein Sauerteig ist heute endlich richtig aufgegangen",
            "Langsam geroestetes Gemuese schmeckt einfach besser",
        ],
        "fr": [
            "Mon levain a enfin bien leve apres trois jours",
            "Les legumes rotis lentement sont tellement meilleurs",
        ],
    },
    "seyahat": {
        "tr": [
            "Karadeniz yaylalarinda uc gun gecirdik manzara tarif edilemez",
            "Ucus rotasi degisti ve aktarma suresi iki saate dustu",
            "Sirt cantasiyla seyahat etmek otelde kalmaktan daha ogretici",
            "Sehirdeki eski mahalleyi yuruyerek gezmek en iyisi",
        ],
        "en": [
            "Spent three days hiking in the mountains and it reset my brain",
            "Traveling with just a backpack teaches you what you actually need",
            "The old quarter of this city is best explored on foot",
            "Missed my connection but ended up seeing a whole new city",
        ],
        "de": [
            "Drei Tage in den Bergen gewandert und es war herrlich",
            "Mit nur einem Rucksack zu reisen ist sehr befreiend",
        ],
        "fr": [
            "Trois jours de randonnee en montagne et je me sens revivre",
            "Voyager avec juste un sac a dos change la perspective",
        ],
    },
    "oyun": {
        "tr": [
            "Bu oyunun hikaye anlatimi son yillarin en iyisi bence",
            "Yeni yamada denge ayarlari sonunda mantikli hale geldi",
            "Kooperatif modda arkadaslarla oynamak cok daha eglenceli",
            "Indie oyunlar buyuk yapimlardan daha yaratici olabiliyor",
        ],
        "en": [
            "The storytelling in this game is better than most films",
            "The latest patch finally fixed the balance issues everyone hated",
            "Playing co op with friends turns an average game into a great one",
            "Indie games keep out innovating the big studio releases",
        ],
        "de": [
            "Die Geschichte in diesem Spiel ist wirklich aussergewoehnlich",
            "Der neue Patch hat die Balance endlich verbessert",
        ],
        "fr": [
            "La narration de ce jeu est meilleure que beaucoup de films",
            "Le dernier patch a enfin corrige les problemes d equilibrage",
        ],
    },
    "bilim": {
        "tr": [
            "Teleskop goruntuleri evrenin ne kadar buyuk oldugunu hatirlatiyor",
            "Iklim modellerindeki belirsizlikler hala cok tartisiliyor",
            "Hucre biyolojisinde yeni bir mekanizma kesfedilmis",
            "Kuantum hesaplama hala erken asamada ama ilerleme var",
        ],
        "en": [
            "These telescope images are a reminder of how small we are",
            "The uncertainty ranges in climate models deserve more attention",
            "A new cellular mechanism was described in this week's paper",
            "Quantum computing is early but the progress is real",
        ],
        "de": [
            "Diese Teleskopbilder zeigen wie klein wir wirklich sind",
            "Quantencomputing steckt noch in den Anfaengen",
        ],
        "fr": [
            "Ces images du telescope rappellent notre petitesse",
            "L informatique quantique progresse lentement mais surement",
        ],
    },
    "finans": {
        "tr": [
            "Enflasyon verileri beklentilerin uzerinde geldi piyasa tepki verdi",
            "Uzun vadeli endeks yatirimi kisa vadeli islemden daha mantikli",
            "Merkez bankasi faiz kararini degistirmedi",
            "Butce planlamasi yapmadan tasarruf etmek cok zor",
        ],
        "en": [
            "Inflation data came in above expectations and markets reacted",
            "Long term index investing beats active trading for most people",
            "The central bank held rates steady again this quarter",
            "Budgeting properly changed my relationship with money",
        ],
        "de": [
            "Die Inflationsdaten lagen ueber den Erwartungen",
            "Langfristiges Investieren schlaegt kurzfristigen Handel",
        ],
        "fr": [
            "Les donnees d inflation depassent les attentes du marche",
            "L investissement a long terme reste la meilleure strategie",
        ],
    },
    "saglik": {
        "tr": [
            "Duzenli uyku duzeni kurmak enerjimi tamamen degistirdi",
            "Gunde on bin adim hedefi basta zor sonra aliskanlik oluyor",
            "Meditasyon uygulamalarini denedim odaklanmama yardimci oldu",
            "Su icmeyi hatirlamak icin alarm kurmak zorunda kaldim",
        ],
        "en": [
            "Fixing my sleep schedule changed my energy levels completely",
            "The ten thousand step goal is hard until it becomes a habit",
            "Meditation actually helped my focus more than I expected",
            "Had to set alarms just to remember to drink water",
        ],
        "de": [
            "Ein fester Schlafrhythmus hat meine Energie veraendert",
            "Meditation hilft mir mehr als ich erwartet hatte",
        ],
        "fr": [
            "Un rythme de sommeil regulier a change mon energie",
            "La meditation m aide vraiment a mieux me concentrer",
        ],
    },
    "sanat": {
        "tr": [
            "Muzedeki sergi beklentimin cok uzerindeydi",
            "Suluboya calismaya basladim sabir gerektiren bir is",
            "Fotografcilikta isik her seyden daha onemli",
            "Eski film afislerini toplamak guzel bir hobi haline geldi",
        ],
        "en": [
            "The exhibition at the museum exceeded every expectation",
            "Started watercolor painting and it demands real patience",
            "In photography light matters more than the camera body",
            "Collecting vintage film posters became an unexpected hobby",
        ],
        "de": [
            "Die Ausstellung im Museum war beeindruckend",
            "Ich habe mit Aquarellmalerei angefangen",
        ],
        "fr": [
            "L exposition au musee a depasse mes attentes",
            "J ai commence l aquarelle et cela demande de la patience",
        ],
    },
}

TOPIC_NAMES = list(TOPICS.keys())

# Konu bazli hashtag havuzu -- tweet hashtags alanini doldurmak icin
HASHTAGS = {
    "teknoloji": ["spark", "kafka", "scala", "kubernetes", "gpu", "distributed"],
    "spor": ["football", "basketball", "marathon", "training"],
    "muzik": ["music", "guitar", "vinyl", "concert"],
    "yemek": ["food", "recipe", "sourdough", "coffee"],
    "seyahat": ["travel", "hiking", "backpacking"],
    "oyun": ["gaming", "indiegames", "coop"],
    "bilim": ["science", "astronomy", "quantum", "research"],
    "finans": ["finance", "investing", "markets"],
    "saglik": ["health", "sleep", "fitness", "meditation"],
    "sanat": ["art", "photography", "painting"],
}


# Metin cesitliligini artiran ekler. Sabit sablon havuzu tek basina
# kullanildiginda ayni cumle yuzlerce kez uretiliyor ve feed'de tekrar
# eden sonuclar olusuyordu. Bu ekler anlami degistirmeden metinleri
# birbirinden ayirir.
PREFIXES = {
    "tr": ["", "Bugun fark ettim: ", "Kisa not: ", "Nihayet! ", "Dusunuyorum da, ",
           "Itiraf ediyorum: ", "Uzun zamandir ", "Sonunda "],
    "en": ["", "Just realized: ", "Quick note: ", "Finally! ", "Honestly, ",
           "Been thinking: ", "Hot take: ", "After weeks of trying, "],
    "de": ["", "Endlich! ", "Kurz notiert: ", "Ehrlich gesagt, ", "Heute gemerkt: "],
    "fr": ["", "Enfin! ", "Petite note: ", "Honnetement, ", "Je viens de realiser: "],
}

SUFFIXES = {
    "tr": ["", " Tavsiye ederim.", " Baska fikri olan var mi?", " Cok memnunum.",
           " Devam edecegim.", " Hala ogreniyorum."],
    "en": ["", " Highly recommend.", " Anyone else?", " Really happy with it.",
           " Will keep going.", " Still learning though."],
    "de": ["", " Sehr zu empfehlen.", " Geht es jemandem auch so?", " Bin zufrieden."],
    "fr": ["", " Je recommande.", " Quelqu un d autre?", " Tres content du resultat."],
}


def pick_text(rng: random.Random) -> tuple[str, str, str, list[str]]:
    """Rastgele bir (konu, dil, metin, hashtag listesi) dondurur."""
    topic = rng.choice(TOPIC_NAMES)
    lang = rng.choice([lg for lg in LANGUAGES if lg in TOPICS[topic]])
    base = rng.choice(TOPICS[topic][lang])

    # Sablonu on/son eklerle cesitlendir -- konu anlami korunur
    prefix = rng.choice(PREFIXES.get(lang, [""]))
    suffix = rng.choice(SUFFIXES.get(lang, [""]))
    text = f"{prefix}{base}{suffix}"

    tags: list[str] = []
    if rng.random() < 0.4:
        pool = HASHTAGS[topic]
        tags = rng.sample(pool, k=min(rng.randint(1, 2), len(pool)))

    return topic, lang, text, tags
