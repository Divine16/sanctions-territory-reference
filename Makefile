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

clean:
	rm -f docs/index.html docs/feed.json
