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

# Install the exact, fully-resolved versions used for the archived release
# (see requirements.lock at the repo root for provenance/regeneration notes).
# Versions are inlined rather than COPYing requirements.lock: environment
# builders (e.g. Code Ocean) build this image before the repository's files
# are available, so COPY from the repo is not possible at this stage.
RUN pip install --no-cache-dir \
      "contourpy==1.3.3" "cycler==0.12.1" "et_xmlfile==2.0.0" "fonttools==4.63.0" \
      "joblib==1.5.3" "kiwisolver==1.5.0" "matplotlib==3.11.0" "narwhals==2.22.1" \
      "numpy==2.4.6" "openpyxl==3.1.5" "packaging==26.2" "pandas==3.0.3" \
      "patsy==1.0.2" "pillow==12.2.0" "pyparsing==3.3.2" "python-dateutil==2.9.0.post0" \
      "scikit-learn==1.9.0" "scipy==1.17.1" "seaborn==0.13.2" "six==1.17.0" \
      "statsmodels==0.14.6" "threadpoolctl==3.6.0"
