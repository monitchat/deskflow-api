#!/bin/sh

# Start PostgreSQL container
docker run -it --name postgres-test -e POSTGRESS_USER=postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres:11
until docker logs postgres-test | grep -q "database system is ready to accept connections" ; do
  echo "Waiting for PostgreSQL container to be available..."
  sleep 1
done

docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3.10-management
until docker logs rabbitmq | grep -q "Ready to start client connection listeners" ; do
  echo "Waiting for Rabbitmq container to be available..."
  sleep 1
done

exit 0
