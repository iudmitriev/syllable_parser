.PHONY: setup run dev clean help

M2M_DIR  := m2m-aligner
M2M_BIN  := $(M2M_DIR)/m2m-aligner
M2M_REPO := https://github.com/letter-to-phoneme/m2m-aligner.git

NLTK_PACKAGES := averaged_perceptron_tagger_eng averaged_perceptron_tagger cmudict

help:
	@echo "Available targets:"
	@echo "  setup  - Install everything: m2m-aligner, Python deps, NLTK data"
	@echo "  run    - Start the production server (gunicorn on :5000)"
	@echo "  dev    - Start the Flask dev server (debug mode on :5000)"
	@echo "  clean  - Remove m2m-aligner clone and Python caches"

setup: $(M2M_BIN) python-deps nltk-data
	@echo "==> Setup complete. Run 'make run' or 'make dev'."

$(M2M_BIN):
	@echo "==> Cloning and building m2m-aligner..."
	@if [ ! -d "$(M2M_DIR)" ]; then \
		git clone $(M2M_REPO) $(M2M_DIR); \
	fi
	@# Strip -lgcc_s: GCC-specific lib not present on macOS/clang, auto-linked on Linux anyway.
	@sed -i.bak 's/-lgcc_s //g' $(M2M_DIR)/Makefile && rm -f $(M2M_DIR)/Makefile.bak
	$(MAKE) -C $(M2M_DIR)

python-deps:
	@echo "==> Installing Python dependencies..."
	uv sync

nltk-data: python-deps
	@echo "==> Downloading NLTK resources..."
	@uv run python -c "import nltk; [nltk.download(p, quiet=True) for p in '$(NLTK_PACKAGES)'.split()]"

run:
	uv run gunicorn -w 4 -b 0.0.0.0:5000 server:app

dev:
	uv run python server.py

clean:
	rm -rf $(M2M_DIR)
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
