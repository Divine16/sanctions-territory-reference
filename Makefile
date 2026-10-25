.PHONY: validate build staleness clean

validate:
	python3 scripts/validate.py

build:
	python3 scripts/build.py

staleness:
	python3 scripts/validate.py --staleness 90

clean:
	rm -f docs/index.html docs/feed.json
