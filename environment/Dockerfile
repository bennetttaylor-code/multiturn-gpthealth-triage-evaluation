FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive \
    MPLBACKEND=Agg \
    PYTHONUNBUFFERED=1

# Microsoft core fonts (provides Arial) so figures render with the publication font on Linux.
RUN printf 'deb http://deb.debian.org/debian bookworm contrib non-free non-free-firmware\n' >> /etc/apt/sources.list \
 && apt-get update \
 && echo "ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula select true" | debconf-set-selections \
 && apt-get install -y --no-install-recommends ttf-mscorefonts-installer fontconfig \
 && fc-cache -f \
 && rm -rf /var/lib/apt/lists/*

# Install the exact, fully-resolved versions used for the archived release.
# Build context is the repo root: docker build -f environment/Dockerfile .
COPY requirements.lock /tmp/requirements.lock
RUN pip install --no-cache-dir -r /tmp/requirements.lock
