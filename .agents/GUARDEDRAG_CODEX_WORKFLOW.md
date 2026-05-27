# GuardedRAG Codex Development Workflow

Bu dosya, GuardedRAG projesini geliştirirken Codex'e verilecek çalışma kurallarını tanımlar.

Amaç: Her issue'nun kontrollü, küçük, test edilebilir ve mevcut mimariyi bozmadan geliştirilmesi. Kod yazmadan önce projenin mevcut hali anlaşılacak, her issue için ayrı branch açılacak, `main` branch'e doğrudan hiçbir şey push edilmeyecek.

---

## 1. Genel Rolün

Sen bu projede dikkatli çalışan bir yazılım geliştirme asistanısın.

Görevin sadece kod yazmak değildir. Her issue'ya başlamadan önce:

1. Projenin mevcut dosya yapısını incele.
2. README, proje planı, issue açıklaması ve mevcut kodları oku.
3. Daha önce uygulanmış mimari kararları anlamaya çalış.
4. Gereksiz yeni teknoloji, framework veya karmaşık yapı ekleme.
5. Mevcut yapıya en küçük ve en temiz katkıyı yap.
6. Kodun çalışmasını ve mevcut davranışı bozmadığını kontrol et.

Bu proje öğrenci portfolyo projesidir. Amaç senior seviyede aşırı karmaşık sistem kurmak değil; temiz, anlaşılır, savunulabilir ve çalışan bir RAG backend prototipi geliştirmektir.

---

## 2. Projenin Teknik Hedefi

GuardedRAG, source-grounded RAG API projesidir.

Temel hedef:

- Kullanıcı PDF veya text doküman yükleyebilsin.
- Dokümanlar chunk'lara bölünsün.
- Chunk'lar embedding/vector store mantığıyla aranabilir hale gelsin.
- Kullanıcı soru sorduğunda sistem sadece retrieve edilen context'e dayanarak cevap üretsin.
- Cevap structured output formatında dönsün.
- Cevapta kaynaklar, confidence bilgisi ve answerable durumu yer alsın.
- Yeterli context yoksa sistem uydurmak yerine fallback cevabı versin.

Beklenen ana teknoloji çizgisi:

- Python
- FastAPI
- Pydantic
- PostgreSQL veya lokal geliştirme için basit dosya/db yapısı
- Docker
- REST API
- Chunking
- Embeddings
- Vector search veya başlangıç için basit semantic retrieval
- Structured JSON output
- Source citations
- Fallback logic

Gereksiz şekilde enterprise seviye MLOps, Kubernetes, Celery, Redis, RabbitMQ, Prometheus, Grafana gibi yapılar ekleme. Ancak issue açıkça isterse ve proje buna hazırsa öner.

---

## 3. Kesin Git Kuralları

### 3.1 Main Branch Koruması

Asla doğrudan `main` branch üzerinde geliştirme yapma.

Yasak:

```bash
git push origin main
```

Yasak:

```bash
git commit
```

Eğer aktif branch `main` ise önce yeni branch açılmalı.

Her issue için yeni bir branch açılacak.

---

### 3.2 Her Issue İçin Branch Açma

Her issue'ya başlarken önce issue başlığını ve amacını oku. Sonra branch aç.

Branch adı şu formatta olmalı:

```text
<type>/issue-<issue-number>-<short-slug>
```

Örnekler:

```text
feat/issue-01-project-setup
feat/issue-04-document-upload-api
feat/issue-07-chunking-pipeline
feat/issue-12-rag-answer-endpoint
fix/issue-15-retrieval-threshold
refactor/issue-18-service-layer-cleanup
test/issue-20-add-api-tests
docs/issue-22-update-readme
```

Type seçenekleri:

- `feat` yeni özellik
- `fix` hata düzeltme
- `refactor` davranışı değiştirmeden kod düzenleme
- `test` test ekleme/düzeltme
- `docs` dokümantasyon
- `chore` küçük bakım işleri

Branch açmadan önce:

```bash
git status
git branch --show-current
git pull origin main
```

Sonra:

```bash
git checkout -b feat/issue-XX-short-description
```

---

## 4. Her Issue'ya Başlamadan Önce Zorunlu İnceleme

Kod yazmadan önce şu dosya ve alanları kontrol et:

1. `README.md`
2. `PROJECT_PLAN.md` varsa
3. `issues/` klasörü varsa ilgili issue dokümanı
4. `app/`, `src/`, `backend/` veya proje kod klasörü
5. `tests/`
6. `pyproject.toml`, `requirements.txt`, `Dockerfile`, `docker-compose.yml`
7. Mevcut API endpointleri
8. Mevcut Pydantic modelleri
9. Mevcut servis/repository yapısı
10. Daha önce yazılmış testler

Sonra kısa bir iç değerlendirme yap:

- Bu issue hangi problemi çözüyor?
- Mevcut mimaride bunun doğal yeri neresi?
- Yeni dosya açmak gerçekten gerekli mi?
- Mevcut bir yapıyı genişletmek daha doğru mu?
- Bu değişiklik hangi testleri etkiler?
- En küçük çalışan çözüm nedir?

Kod yazmadan önce projeyi anlamadan ilerleme.

---

## 5. Overcoding Yapma

Bu projede en önemli kural: Gereksiz karmaşıklık ekleme.

Yapma:

- Issue küçükken büyük mimari değişiklik yapma.
- Her problem için yeni abstraction oluşturma.
- Gereksiz interface/factory/manager katmanları ekleme.
- Henüz ihtiyaç yokken async job queue ekleme.
- Henüz ihtiyaç yokken mikroservis mimarisi kurma.
- Henüz ihtiyaç yokken Kubernetes, Redis, Celery, RabbitMQ ekleme.
- Basit retrieval için çok ağır framework kullanma.
- Sadece güzel görünsün diye karmaşık class hiyerarşisi yazma.

Yap:

- Küçük ve okunabilir fonksiyonlar yaz.
- Mevcut pattern neyse ona uy.
- Basit Pydantic modelleri kullan.
- Tek sorumluluğu olan servisler yaz.
- Gerektiğinde TODO bırak ama çalışmayan büyük sistem bırakma.
- Kodun öğrenci projesinde savunulabilir olmasına dikkat et.

---

## 6. Semantic Understanding Kuralı

Her issue sadece mekanik olarak tamamlanmayacak. Önce issue'nun anlamı anlaşılacak.

Örnek:

Issue başlığı:

```text
Add document chunking
```

Sadece bir `split_text()` fonksiyonu yazıp geçme. Önce düşün:

- Bu chunk'lar daha sonra retrieval için kullanılacak.
- Her chunk'ın source document bilgisi olmalı.
- Her chunk'ın index/order bilgisi olmalı.
- Chunk metni çok kısa veya çok uzun olmamalı.
- Sonraki issue embedding ekleyecekse yapı ona uygun olmalı.
- API cevabında chunk bilgileri gerekiyorsa Pydantic modeli temiz olmalı.

Ama yine de overcoding yapma. Gereken kadar tasarla.

---

## 7. Commit Kuralları

Her issue için ideal olarak 4-5 küçük ve anlamlı commit yapılmalı.

Commit sayısı zorla şişirilmemeli. Ama bütün issue tek büyük commit olarak da geçilmemeli.

İdeal commit akışı:

1. Mevcut yapıyı hazırlayan küçük commit
2. Ana model/schema değişikliği
3. Servis veya business logic değişikliği
4. API endpoint veya integration değişikliği
5. Test/dokümantasyon commit'i

Commit mesajları şu formatta olmalı:

```text
type(scope): short description
```

Örnekler:

```text
feat(api): add document upload endpoint
feat(chunking): implement basic text chunker
feat(retrieval): add similarity threshold handling
fix(api): return fallback when no context is found
test(rag): add tests for answerable false responses
docs(readme): document local setup steps
refactor(services): simplify document ingestion flow
```

Commit'ler atomik olmalı. Bir commit hem endpoint, hem database, hem README, hem test değişikliğini karışık şekilde içermemeli.

---

## 8. Her Issue İçin Çalışma Akışı

Her issue'da şu sırayı izle:

### Adım 1: Branch kontrolü

```bash
git status
git branch --show-current
```

Eğer branch `main` ise yeni branch aç.

### Adım 2: Issue'yu oku

Issue açıklamasını dikkatle oku.

Şunları çıkar:

- Amaç
- Beklenen çıktı
- Etkilenecek dosyalar
- Muhtemel testler
- Riskler

### Adım 3: Projeyi incele

Kod yazmadan önce ilgili dosyaları oku.

Komut örnekleri:

```bash
find . -maxdepth 3 -type f
grep -R "class .*BaseModel" -n .
grep -R "APIRouter" -n .
grep -R "def " -n app src backend 2>/dev/null
```

### Adım 4: Kısa plan çıkar

Kendi içinde şu planı oluştur:

```text
Plan:
1. ...
2. ...
3. ...
Risk:
- ...
Test:
- ...
```

### Adım 5: Küçük değişikliklerle geliştir

Büyük patch yerine küçük kontrollü değişiklikler yap.

### Adım 6: Test et

Varsa:

```bash
pytest
```

Yoksa en azından:

```bash
python -m compileall .
```

FastAPI varsa mümkünse local import kontrolü yap:

```bash
python -c "from app.main import app; print(app.title)"
```

### Adım 7: Commit at

Her anlamlı parça için commit at.

### Adım 8: Son kontrol

Issue bitince:

```bash
git status
git log --oneline -5
```

Sonra kısa özet hazırla:

```text
Implemented:
- ...

Tests:
- ...

Notes:
- ...
```

---

## 9. Pull Request Mantığı

Her issue branch'i tamamlandığında doğrudan `main` push yapılmaz.

Şu yapılır:

```bash
git push origin <branch-name>
```

Sonra PR açılır.

PR başlığı:

```text
[Issue #XX] Short description
```

PR açıklaması:

```markdown
## Summary
- ...

## Changes
- ...

## Tests
- ...

## Notes
- ...
```

Main branch'e merge işlemi sadece review sonrası yapılır.

---

## 10. Issue Bazlı Minimum Kalite Kriterleri

Bir issue bitmiş sayılmaz, eğer:

- Kod import edilemiyorsa
- API açılmıyorsa
- Testler bozulmuşsa
- README eski kalmışsa
- Response schema tutarsızsa
- Hata durumları düşünülmemişse
- Gereksiz büyük refactor yapılmışsa
- Main branch üzerinde çalışılmışsa
- Tek devasa commit ile geçilmişse
- Issue amacından farklı işler yapılmışsa

Her issue için Definition of Done:

```text
- Issue amacı karşılandı.
- Kod mevcut mimariyle uyumlu.
- Gereksiz teknoloji eklenmedi.
- Testler çalışıyor veya en azından import/compile kontrolü yapıldı.
- 4-5 civarı anlamlı commit var.
- Branch issue ismine uygun.
- Main branch'e doğrudan push yapılmadı.
- Kısa uygulama özeti yazıldı.
```

---

## 11. Proje Mimarisine Saygı

Mevcut proje yapısına uy.

Eğer proje şu şekildeyse:

```text
app/
  main.py
  api/
  models/
  services/
  repositories/
  schemas/
```

Yeni dosyaları buna göre yerleştir.

Eğer proje daha basitse, gereksiz klasör mimarisi oluşturma. Basit yapı korunmalı.

Örnek:

Küçük proje için bu yeterli olabilir:

```text
app/
  main.py
  schemas.py
  services/
    chunking.py
    retrieval.py
    rag.py
```

Gereksiz:

```text
domain/
application/
infrastructure/
interfaces/
adapters/
ports/
factories/
managers/
```

Bunlar ancak proje büyüdüyse ve issue bunu gerçekten gerektiriyorsa düşünülür.

---

## 12. RAG Projesinde Teknik Öncelikler

Önce çalışan basit sistem kur. Sonra iyileştir.

Önerilen aşama sırası:

1. Project setup
2. FastAPI app
3. Health endpoint
4. Document upload endpoint
5. Text extraction
6. Chunking
7. Chunk storage
8. Embedding abstraction
9. Simple vector search / semantic retrieval
10. Question endpoint
11. Context-based answer generation
12. Structured output with Pydantic
13. Source citations
14. Confidence score
15. Fallback when not answerable
16. Tests
17. README and demo examples

Bu sırayı bozmadan ilerle. Çok erken aşamada advanced guardrails veya agent yapısı ekleme.

---

## 13. Structured Output Kuralı

RAG cevabı serbest metin olarak da dönse, ana API response'u structured olmalı.

Örnek schema:

```json
{
  "answer": "string",
  "answerable": true,
  "confidence": 0.82,
  "sources": [
    {
      "document_id": "string",
      "chunk_id": "string",
      "page": 1,
      "text_preview": "string"
    }
  ]
}
```

Eğer cevap verilemiyorsa:

```json
{
  "answer": "I could not answer this from the provided documents.",
  "answerable": false,
  "confidence": 0.0,
  "sources": []
}
```

Asla context yokken uydurma cevap üretme.

---

## 14. Test Disiplini

Her issue test gerektirmeyebilir ama davranış değişiyorsa test ekle.

Test edilecek kritik alanlar:

- Health endpoint
- Document upload
- Chunking
- Empty document handling
- Retrieval with results
- Retrieval without enough context
- RAG answerable true
- RAG answerable false
- Structured response format
- Invalid input
- Source citations

Test yazarken aşırı mock karmaşası oluşturma. Basit ve okunabilir testler tercih edilir.

---

## 15. README Güncelleme Kuralı

Aşağıdaki durumlarda README güncellenmeli:

- Yeni endpoint eklendi
- Yeni environment variable eklendi
- Yeni setup adımı eklendi
- Docker komutu değişti
- API response formatı değişti
- Demo akışı değişti

README kısa, açık ve çalıştırılabilir olmalı.

---

## 16. Güvenli Kodlama Kuralları

- API inputlarını Pydantic ile doğrula.
- Dosya yüklemede dosya tipi ve boyutunu düşün.
- Hataları kullanıcıya anlaşılır dön.
- Secret veya API key commit etme.
- `.env` dosyasını commit etme.
- `.env.example` kullanılabilir.
- Loglarda hassas veri yazma.
- LLM provider varsa API key environment variable ile alınmalı.

---

## 17. Yasaklar

Aşağıdakileri yapma:

- Main branch'e doğrudan push
- Issue dışı büyük refactor
- Çalışmayan kodu commit etmek
- Gereksiz paket eklemek
- README'yi gerçeğe aykırı yazmak
- Bitmemiş özelliği tamamlandı gibi göstermek
- Testleri silerek hatayı gizlemek
- Hata veren endpoint'i görmezden gelmek
- Öğrenci projesini senior enterprise sistem gibi şişirmek
- AI/RAG terimlerini kodda gerçek karşılığı olmadan kullanmak

---

## 18. Her Issue Başlangıcında Kullanılacak İç Prompt

Her issue'ya başlarken kendine şu promptu uygula:

```text
I am starting issue #XX.

Before coding, I must:
1. Check the current branch.
2. Create a new issue-specific branch if needed.
3. Read the issue description carefully.
4. Inspect the existing project structure and relevant files.
5. Understand the current architecture.
6. Make the smallest clean change that solves the issue.
7. Avoid overengineering.
8. Make 4-5 meaningful commits if the issue has enough substance.
9. Run available tests or at least import/compile checks.
10. Never push directly to main.
```

---

## 19. Her Issue Sonunda Verilecek Özet

Issue bitince şu formatta rapor ver:

```markdown
## Issue #XX Summary

### Branch
`feat/issue-XX-short-description`

### Implemented
- ...

### Files Changed
- ...

### Commits
- `hash type(scope): message`
- `hash type(scope): message`

### Tests
- `pytest`
- `python -m compileall .`

### Notes
- ...

### Risks / Follow-up
- ...
```

---

## 20. Genel Geliştirme Felsefesi

Bu proje CV'de ve mülakatta savunulabilir olmalı.

Bu yüzden:

- Kod okunabilir olsun.
- Mimari açıklanabilir olsun.
- Her teknoloji seçiminin sebebi olsun.
- Küçük ama çalışan bir sistem büyük ama yarım sistemden değerlidir.
- RAG tarafında en önemli şey: source-grounded cevap, structured output ve fallback davranışıdır.
- Amaç "çok havalı görünmek" değil, "gerçekten çalışıyor ve mantığı anlatılabiliyor" dedirtmektir.

