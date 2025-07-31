FROM python:3.12-slim

# Install Poetry
RUN pip install poetry

# Set working directory
WORKDIR /app

# Copy project files
COPY  . ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# COPY . .

RUN pip install .

CMD ["easyconvert", "--help"]