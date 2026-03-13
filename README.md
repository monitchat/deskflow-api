# Preparar ambiente local

## Criar e ativar virtualenv

    $ python3.9 -m venv venv
    $ source venv/bin/activate

## Instalar utilitários

    $ pip install --upgrade pip setuptools

## Instalar dependências

    $ pip install -e .
    $ pip install pytest pytest-cov pre-commit flake8 isort black gunicorn

## Instalar git pre-commit hooks

    $ pre-commit install
    $ pre-commit autoupdate

## Iniciar PostgreSQL local

    $ tests/resources/database/run-container.sh
    $ tests/resources/database/seed-database.sh

# Desenvolvimento

## Executar testes

    $ scripts/run-tests.sh

## Tunnel para receber callbacks em Dev

O tunnel abaixo irá possibilitar receber os callbacks da Omnichat em `localhost:5000`

    ssh -R 5000:localhost:5000 -i deskflow-dev_key.pem ubuntu@deskflow-dev.eastus2.cloudapp.azure.com 'sudo killall -9 socat 2>/dev/null ; sudo socat TCP-LISTEN:80,fork,reuseaddr TCP:localhost:5000'

## RabbitMQ

docker run -d --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3.10-management
