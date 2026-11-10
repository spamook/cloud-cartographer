# Sample app

This is a sample app with React frontend, Go backend and Postgres database.

It allows users to register, login and logout.
Accounts are stored in Postgres database.

[Go fiber](https://github.com/gofiber/fiber) framework is used for backend.

## Usage

### Build images

```
docker compose build
```

### Run application

```
docker compose up -d
```

### Access frontend

```
http://localhost:3000
```

### Clean up

```
docker compose down -v
```

## Endpoints

| endpoint      | method | body                                           | description       |
| ------------- | ------ | ---------------------------------------------- | ----------------- |
| /api/ping     | GET    |                                                | ping server       |
| /api/session  | GET    |                                                | get user session  |
| /api/login    | POST   | { email String, password String }              | login user        |
| /api/register | POST   | { email String, password String, name String } | register new user |
|               |        |                                                |                   |
