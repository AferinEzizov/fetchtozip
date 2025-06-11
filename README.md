# FetchtoZip


**FetchtoZip** HTTP API-lərdən məlumat yükləyən, onu emal edən və ZIP arxivlərinə çevirən yüksək performanslı asinxron mikroxidmətdir. Müasir Python texnologiyaları ilə korporativ səviyyədə performans və miqyaslanma üçün yaradılmışdır.

## Əsas Xüsusiyyətlər

- **Yüksək Performans**: Polars istifadə edərək pandas-dan 8-10 dəfə sürətli
- **Asinxron Arxitektura**: FastAPI ilə bloklaşmayan əməliyyatlar
- **Məlumat Manipulyasiyası**: Sütun dəyişmə, filtrleme və transformasiya
- **Real-vaxt İzləmə**: WebSocket əsaslı status bildirişləri
- **Çoxlu Format Dəstəyi**: CSV, Excel, JSON emalı
- **Arxa Plan Tapşırıqları**: Effektiv növbə əsaslı iş idarəetməsi

## Arxitektura

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI        │    │   Məlumat       │
│   (React/JS)    │◄──►│   Backend        │◄──►│   Qatı          │
│                 │    │                  │    │   (Polars)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   WebSocket     │    │   Arxa Plan      │    │   Fayl Sistemi  │
│   Bildirişləri  │    │   Tapşırıqları   │    │   (ZIP/Excel)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Quraşdırma

### Tələblər

- Python 3.9+
- pip və ya conda

### Addımlar

1. **Repository-ni klonlayın**
   ```bash
   git clone https://github.com/AferinEzizov/fetchtozip.git
   cd fetchtozip
   ```

2. **Asılılıqları quraşdırın**
   ```bash
   pip install -r requirements.txt
   ```

3. **Mühiti konfiqurasiya edin**
   ```bash
   cp .env.example .env
   # .env faylını redaktə edin
   ```

4. **Tətbiqi işə salın**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **API-yə daxil olun**
   - API Sənədləri: http://localhost:8000/docs
   - Sağlamlıq Yoxlaması: http://localhost:8000/health

## Performans Göstəriciləri

| Əməliyyat | Pandas | Polars | Təkmilləşmə |
|-----------|--------|---------|-------------|
| CSV Oxuma (1M+ sətir) | ~12s | ~1.5s | **8x sürətli** |
| Məlumat Filtrləmə | ~4.5s | ~0.4s | **10x sürətli** |
| GroupBy + Aqreqasiya | ~6s | ~0.6s | **10x sürətli** |
| Yaddaş İstifadəsi | 2-3 GB | 0.5-1 GB | **3x az** |

## API Arayışı

### Əsas Nöqtələr

| Metod | Nöqtə | Təsvir | Status |
|--------|----------|-------------|---------|
| `POST` | `/api/v1/input` | Sütun konfiqurasiyası əlavə et | Aktiv |
| `POST` | `/api/v1/start` | Emal tapşırığını başlat | Aktiv |
| `GET` | `/api/v1/status/{task_id}` | Tapşırıq statusunu əldə et | Aktiv |
| `GET` | `/api/v1/download/{task_id}` | ZIP faylını yüklə | Aktiv |
| `WS` | `/api/v1/ws/{task_id}` | Real-vaxt bildirişləri | Aktiv |

### İstifadə Nümunələri

#### 1. Məlumat Emalını Konfiqurasiya Et
```bash
curl -X POST "http://localhost:8000/api/v1/input" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "gəlir_sütunu",
    "column": 3,
    "change_order": 1
  }'
```

#### 2. Emalı Başlat
```bash
curl -X POST "http://localhost:8000/api/v1/start"
```

Cavab:
```json
{
  "message": "Export başladı",
  "task_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

#### 3. Proqresi İzlə (WebSocket)
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/123e4567-e89b-12d3-a456-426614174000');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Status:', data.status); // started, processing, completed, failed
};
```

## İnkişaf

### Layihə Strukturu

```
fetchtozip/
├── app/
│   ├── api/                    # API marşrutları və nöqtələr
│   │   └── routes.py
│   ├── core/                   # Konfiqurasiya və parametrlər
│   │   └── config.py
│   ├── services/               # Biznes məntiq qatı
│   │   └── data.py
│   ├── models/                 # Pydantic modelləri
│   └── main.py                 # FastAPI tətbiqi
├── temp/                       # Müvəqqəti fayl saxlama
├── tests/                      # Test dəstləri
├── requirements.txt
└── README.md
```

### Testlərin İşlədilməsi

```bash
# Test asılılıqlarını quraşdır
pip install pytest pytest-asyncio

# Testləri işlət
pytest tests/ -v

# Əhatə ilə işlət
pytest tests/ --cov=app --cov-report=html
```

## Docker Yerləşdirilməsi

### Qurmaq və İşlətmək

```bash
# Image qur
docker build -t fetchtozip:latest .

# Konteyner işlət
docker run -d \
  --name fetchtozip \
  -p 8000:8000 \
  -v $(pwd)/temp:/app/temp \
  fetchtozip:latest
```

### Docker Compose

```yaml
version: '3.8'
services:
  fetchtozip:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./temp:/app/temp
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=info
```


```json
{
  "timestamp": "2024-01-15T10:30:45Z",
  "level": "INFO",
  "service": "fetchtozip",
  "task_id": "123e4567-e89b-12d3-a456-426614174000",
  "message": "Emal başladı",
  "duration_ms": 1250
}
```

## Konfiqurasiya

### Mühit Dəyişənləri

| Dəyişən | Təsvir | Standart |
|----------|-------------|---------|
| `ENVIRONMENT` | Yerləşdirmə mühiti | `development` |
| `LOG_LEVEL` | Loq səviyyəsi | `info` |
| `TEMP_DIR` | Müvəqqəti fayllar qovluğu | `./temp` |
| `MAX_FILE_SIZE` | Maksimum yükləmə ölçüsü (MB) | `100` |
| `WORKER_TIMEOUT` | Arxa plan tapşırıq vaxt limiti (s) | `300` |

## Töhfə Vermək

İnkişaf iş axını:

1. Repository-ni fork edin
2. Xüsusiyyət branch yaradın (`git checkout -b feature/yeni-xususiyyet`)
3. Dəyişikliklərinizi edin
4. Yeni funksionallıq üçün testlər əlavə edin
5. Bütün testlərin keçdiyinə əmin olun (`pytest`)
6. Dəyişikliklərinizi commit edin (`git commit -m 'Yeni xüsusiyyət əlavə et'`)
7. Branch-ı push edin (`git push origin feature/yeni-xususiyyet`)
8. Pull Request açın

## Məlum Problemlər

- WebSocket bağlantıları yavaş emal tapşırıqlarında vaxt bitə bilər
- Uğursuz tapşırıqlar üçün müvəqqəti fayl təmizləməsi təkmilləşdirilməlidir


## Lisenziya

Bu layihə MIT Lisenziyası altında lisenziyalanmışdır - təfərrüatlar üçün [LICENSE](LICENSE) faylına baxın.
