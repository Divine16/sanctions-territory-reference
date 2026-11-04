.PHONY: validate build staleness exhibits clean

validate:
	python3 scripts/validate.py

build:
	python3 scripts/build.py

staleness:
	python3 scripts/validate.py --staleness 90

exhibits:
	python3 scripts/generate_exhibit_artifacts.py

exhibit-pdf: exhibits
	python3 scripts/exhibit_pdf.py

exhibit-package:
	@command -v google-chrome >/dev/null 2>&1 || command -v google-chrome-stable >/dev/null 2>&1 || \
	  (test -x "$$HOME/.cache/ms-playwright/chromium-"*/chrome-linux64/chrome 2>/dev/null) || \
	  (echo "Installing Playwright Chromium (one-time)…" && playwright install chromium)
	python3 scripts/build_exhibit_package.py
	python3 scripts/exhibit_pdf.py

clean:
	rm -f docs/index.html docs/feed.json
