FROM python:3.12-slim

WORKDIR /app

# install Poetry, configure it, and install only runtime deps
RUN pip install --no-cache-dir poetry \
 && poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-root

# copy your source
COPY scraipe_st ./scraipe_st
COPY .streamlit ./ .streamlit

ENV PYTHONPATH=/app

EXPOSE 8501
ENTRYPOINT ["streamlit", "run", "scraipe_st/app.py", "--server.address=0.0.0.0", "--server.port=8501"]