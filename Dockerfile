FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    AUDIVERIS_BIN=/usr/local/bin/Audiveris

ARG AUDIVERIS_VERSION=5.9.0
ARG AUDIVERIS_UBUNTU_RELEASE=24.04

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    dpkg \
    python3 \
    python3-pip \
    python3-venv \
    openjdk-21-jre-headless \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-nor \
    tesseract-ocr-deu \
    tesseract-ocr-dan \
    xdg-utils \
    shared-mime-info \
    desktop-file-utils \
    libxext6 \
    libxrender1 \
    libxtst6 \
    libxi6 \
    libxrandr2 \
    libfreetype6 \
    fontconfig \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fL "https://github.com/Audiveris/audiveris/releases/download/${AUDIVERIS_VERSION}/Audiveris-${AUDIVERIS_VERSION}-ubuntu${AUDIVERIS_UBUNTU_RELEASE}-x86_64.deb" \
    -o /tmp/audiveris.deb \
    && dpkg-deb -x /tmp/audiveris.deb / \
    && rm -f /tmp/audiveris.deb \
    && rm -rf /var/lib/apt/lists/*

RUN if [ -x /opt/audiveris/bin/Audiveris ]; then \
      ln -sf /opt/audiveris/bin/Audiveris /usr/local/bin/Audiveris; \
    elif [ -x /usr/bin/Audiveris ]; then \
      ln -sf /usr/bin/Audiveris /usr/local/bin/Audiveris; \
    else \
      echo "Audiveris binary not found after package extraction"; \
      exit 1; \
    fi \
    && test -x /usr/local/bin/Audiveris

COPY app.py README.md pyproject.toml ./

RUN python3 -m pip install --break-system-packages \
    streamlit \
    pymupdf \
    pillow \
    music21

EXPOSE 8501

CMD ["python3", "-m", "streamlit", "run", "app.py", "--server.address", "0.0.0.0", "--server.port", "8501"]
