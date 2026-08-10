# Документация: отправка фотографии на email

Сайт собран на MkDocs Material. Исходные материалы находятся в `content`;
они не изменяются при подготовке сайта.

## Локальный запуск

```powershell
python -m pip install -r requirements.txt
python scripts/build_docs.py
python -m mkdocs serve
```

Откройте `http://127.0.0.1:8000/`.

## Режим разработки

```powershell
python scripts/dev_server.py --port 8005
```

Режим разработки следит за изменениями в папке `content`, пересобирает
страницы и автоматически обновляет сайт в браузере.

## Публикация

После загрузки проекта в GitHub откройте **Settings → Pages** и выберите
**GitHub Actions** в качестве источника публикации. Каждый push в ветку
`main` запустит workflow и обновит сайт.
