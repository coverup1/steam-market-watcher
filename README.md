# Steam Market Watcher (CS2)

Bu proje, **Steam Community Market** üzerindeki belirli CS2 skinlerini düzenli olarak izler ve anlık en düşük fiyat, son 24 saatlik ortalama fiyata göre `%10` veya daha fazla düşükse Discord webhook ile bildirim gönderir.

> ⚠️ Bu uygulama **sadece izleme ve bildirim** yapar. Otomatik satın alma içermez.

## Özellikler

- Belirlenen skin listesi için sürekli izleme
- Steam price history ile son 24 saatlik (yoksa mevcut) ağırlıklı ortalama fiyat hesabı
- Steam anlık en düşük fiyat kontrolü
- `%10+` indirim tespitinde Discord bildirimi
- Aynı skin için **30 dakika cooldown** (tekrar bildirim engeli)
- İstekler arasında rastgele bekleme süreleri
  - Her skin sonrası küçük rastgele bekleme
  - Ana döngüde **45–120 saniye** rastgele bekleme
- Hata durumunda kapanmak yerine loglayıp çalışmaya devam etme

## İzlenen Skinler

- AK-47 | Slate (Field-Tested)
- AWP | Atheris (Field-Tested)
- USP-S | Cortex (Field-Tested)
- Glock-18 | Vogue (Field-Tested)
- M4A1-S | Night Terror (Field-Tested)
- AK-47 | Elite Build (Field-Tested)
- AWP | Worm God (Field-Tested)
- M4A4 | Griffin (Field-Tested)
- USP-S | Flashback (Field-Tested)
- FAMAS | Mecha Industries (Field-Tested)

## Proje Yapısı

- `steam_client.py` → Steam API/endpoint veri çekme işlemleri
- `analyzer.py` → Ortalama ve indirim analizi
- `notifier.py` → Discord webhook bildirimi
- `main.py` → Uygulama akışı ve döngü yönetimi
- `requirements.txt` → Gerekli Python paketleri

## Kurulum

1. Python 3.10+ kurulu olduğundan emin olun.
2. Proje klasöründe sanal ortam oluşturup aktif edin (opsiyonel ama önerilir).
3. Bağımlılıkları yükleyin:

```bash
pip install -r requirements.txt
```

4. Proje kök dizininde `.env` dosyası oluşturun:

```env
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

## Çalıştırma (Windows dahil)

Proje kök dizininde:

```bash
python main.py
```

## Çalışma Mantığı

1. Her skin için fiyat geçmişi çekilir.
2. Son 24 saatteki (veri yoksa mevcut tüm) verilerle ağırlıklı ortalama hesaplanır.
3. Anlık en düşük liste fiyatı çekilir.
4. Eğer `anlık <= ortalama * 0.90` ise alarm adayıdır.
5. Son 30 dakika içinde aynı skin için bildirim gönderilmediyse Discord bildirimi yollanır.

## Loglama ve Dayanıklılık

- Hatalar loglanır; uygulama kapanmaz.
- Ağ hatası, JSON parse hatası gibi durumlarda ilgili skin atlanır ve döngü devam eder.

## Notlar

- Steam tarafında rate limit veya geçici erişim kısıtları olabilir; bu yüzden rastgele bekleme süreleri uygulanır.
- Para birimi varsayılan olarak USD (`currency=1`) kullanır.
- Bu proje Steam ToS’a uygun şekilde yalnızca veri izleme / bildirim amacıyla tasarlanmıştır.
