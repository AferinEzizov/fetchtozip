# 📦 FetchtoZip

**FetchtoZip** — API-dən faylları (məsələn, Excel və ya CSV) yükləyən, onları emal edib ZIP arxivinə çevirən asinxron mikroxidmət tətbiqidir.

## Məqsəd

Bu layihənin əsas məqsədi:

- İstənilən **HTTP API-dən məlumatları** (məsələn, Excel və ya CSV) **yükləmək**
- Onları `polars` ilə **emal etmək** (sütun dəyişmək, sıralaq, filtrləmək və s.)
- Faylı **ZIP** formatında **saxlamaq**
- Prosesi **asinxron** və **performanslı** şəkildə idarə etmək
- Frontend üçün **bildiriş əsaslı sistem** yaratmaq – yükləmə tamamlandıqda bildiriş verilir

## ⚙ Texnologiyalar

| Komponent           | Texnologiya          |
|---------------------|----------------------|
| Backend Framework    | [FastAPI](https://fastapi.tiangolo.com/)              |
| Data Processing      | [Polars](https://pola-rs.github.io/polars-book/) (`pandas` alternativi) |
| HTTP Client          | `requests`           |
| Arxivləmə (ZIP)      | `zipfile`            |
| Asinxron Tasklar     | `BackgroundTasks`    |
| Fayl Sistemi         | `temp/` qovluğu      |
| Deployment (plan)    | Docker               |

---

##  Niyə `polars`?

Əvvəlki versiyalarda `pandas` istifadə olunurdu, lakin böyük datasetlərlə işləyərkən performans zəif idi. `polars` aşağıdakı üstünlükləri verir:

### Performans müqayisəsi (`10 milyon sətrlik CSV`)

| Əməliyyat            | Pandas         | Polars        | Fərq     |
|----------------------|----------------|---------------|----------|
| CSV oxumaq           | ~12 saniyə     | ~1.5 saniyə   |  8x     |
| Süzgəc (filter)      | ~4.5 saniyə    | ~0.4 saniyə   |  10x    |
| Groupby + Aggregasiya| ~6 saniyə      | ~0.6 saniyə   |  10x    |
| Yaddaş istifadəsi    | 2–3 GB         | 0.5–1 GB      |  ~3x    |

---

##  Layihə Strukturu

```
app/
├── api/               # FastAPI route-ları
│   └── routes.py
├── core/              # Konfiqurasiya, mühit dəyişkənləri
│   └── config.py
├── services/          # Əsas biznes məntiqi
│   └── fetchtozip.py
├── main.py            # FastAPI tətbiqinin başlanğıcı
temp/                  # Yaradılmış .xlsx və .zip fayllar

```

##  API Endpoint-lər

| Metod | Yol | Açıqlama |
|-------|-----|----------|
| `POST` | `/start-export` | Yeni zip prosesi başladır |
| `GET`  | `/status/{task_id}` | Taskın statusunu qaytarır |
| `GET`  | `/download/{task_id}` | ZIP faylını yükləyir |

---

##  TODO-lar

- [x] ZIP faylının yaradılması
- [x] Polars ilə sütun dəyişməsi və sıralama
- [ ] Download-un düzəldilməsi (`FileResponse` problemi)
- [ ] API URL və path-lərin `config.py`-də saxlanması
- [ ] CSV və JSON dəstəyi
- [ ] Dockerfile ilə deploy
- [ ] Threading/async optimizasiyası

---

## Frontend Tətbiqi

Frontend sadə JavaScript + HTML vasitəsilə:
- `POST /start-export` ilə task yaradır
- `GET /status/{task_id}` ilə progressi `setInterval()` ilə izləyir
- Task tamamlandıqda `download` düyməsi aktiv olur

📎 *Qeyd:* Notification üçün `toastr`, `Snackbar`, və ya `custom modal` istifadə oluna bilər.

---

##  Lisenziya

Bu layihə MIT lisenziyası ilə yayımlanır. İstifadə etməkdə sərbəstsiniz.

---
