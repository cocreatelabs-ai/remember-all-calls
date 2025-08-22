FROM python:3.11-slim

WORKDIR /webapp

RUN pip install uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

EXPOSE 5000

CMD ["uv", "run", "gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--timeout", "120", "--log-level", "debug", "app:app"]