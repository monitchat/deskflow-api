#!/bin/sh

# Create and seed database
docker run --rm --network host -v "$(pwd)"/deploy/database:/scripts -e PGPASSWORD="posgres" postgres:11 psql -h 172.17.0.1 -U postgres -f /scripts/00__create_database.sql
docker run --rm --network host -v "$(pwd)"/deploy/database:/scripts -e PGPASSWORD="<SECRET>" postgres:11 psql -h 172.17.0.1 -U danubio_bot -f /scripts/01__schema.sql
docker run --rm --network host -v "$(pwd)"/deploy/database:/scripts -e PGPASSWORD="<SECRET>" postgres:11 psql -h 172.17.0.1 -U danubio_bot -f /scripts/02__flows_schema.sql
docker run --rm --network host -v "$(pwd)"/deploy/database:/scripts -e PGPASSWORD="<SECRET>" postgres:11 psql -h 172.17.0.1 -U danubio_bot -f /scripts/03__add_flow_id_to_contexts.sql
docker run --rm --network host -v "$(pwd)"/tests/resources/database:/scripts -e PGPASSWORD="<SECRET>" postgres:11 psql -h 172.17.0.1 -U danubio_bot -f /scripts/seed.sql

exit 0
