
# Build go binary.
build:
	cd cmd && go build -o main .

run:
	cd cmd && ./main

build-run: build run

run-tests:
	docker compose -f docker-compose-test.yml up --force-recreate run-tests