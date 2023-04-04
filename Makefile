include .env

.PHONY: start

setup:
	python3 -m pip install --upgrade pip
	python3 -m venv .venv
	source .venv/bin/activate
	pip install -r requirements.txt

start:
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 --env-file .env

ingest:
	(cd src; ../.venv/bin/python ingest.py;)

.PHONY: format
format:
	black .
	isort .

docker-build:
	docker build -t rentagpt .

docker-run:
	export $(cat .env | xargs)
	docker stop rentagpt || true && docker rm rentagpt || true
	docker run --name rentagpt --rm -e OPENAI_API_KEY=${PROVIDERS__OPENAI__API_KEY} -p 8000:8000 rentagpt

docker-logs:
	docker logs -f rentagpt
