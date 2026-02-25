# SETUP

## Install Requirements

```shell
  uv sync
```

## Environment Variables

```shell
  cp .env.example .env
```

## Database Migrations

```shell
  python manager.py makemigrations
  python manager.py migrate
```

## Run Server

```shell
  python manager.py runserver
  uv run python manage.py runserver
```

```账号和密码
    admin
    admin111
```
