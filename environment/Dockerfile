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

# Pinned to the same minimum versions as requirements.txt
RUN pip install --no-cache-dir \
      "pandas>=2.0" "openpyxl>=3.1" "numpy>=1.24" "scipy>=1.11" \
      "scikit-learn>=1.3" "statsmodels>=0.14" "matplotlib>=3.7" "seaborn>=0.12"
