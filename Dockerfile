FROM python:3.13-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml poetry.lock ./
RUN uv pip install --system -r pyproject.toml

COPY src/ ./src/

EXPOSE 5000

CMD ["python", "src/server.py"]