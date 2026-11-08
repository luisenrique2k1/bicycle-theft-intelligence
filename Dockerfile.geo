
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt requirements-geo.txt ./

RUN pip install --no-cache-dir -r requirements-geo.txt

COPY scripts/setup_geography.py scripts/setup_geography.py
COPY scripts/generate_london_map.py scripts/generate_london_map.py

CMD ["sh", "-c", "python scripts/setup_geography.py && python scripts/generate_london_map.py"]
