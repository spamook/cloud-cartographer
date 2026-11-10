package db

import (
	"database/sql"
	"fmt"
	"path/filepath"

	_ "github.com/jackc/pgconn"
	_ "github.com/jackc/pgx/v4"
	_ "github.com/jackc/pgx/v4/stdlib"

	"backend/packages/config"

	"github.com/apex/log"
	"github.com/golang-migrate/migrate/v4"
	"github.com/golang-migrate/migrate/v4/database/postgres"
	_ "github.com/golang-migrate/migrate/v4/source/file"
)

func ConnectDB() (*sql.DB, error) {
	user := config.Config[config.POSTGRES_USER]
	password := config.Config[config.POSTGRES_PASSWORD]
	database := config.Config[config.POSTGRES_DB]
	host := config.Config[config.POSTGRES_SERVER_HOST]

	dsn := fmt.Sprintf("host=%s port=5432 user=%s password=%s dbname=%s sslmode=disable timezone=Europe/Tallinn connect_timeout=5", host, user, password, database)

	db, err := sql.Open("pgx", dsn)
	if err != nil {
		return nil, err
	}

	if err := db.Ping(); err != nil {
		return nil, err
	}
	return db, nil
}

func Migrate(db *sql.DB, dbName string) error {
	log.Info("running db migrations, to disable set RUN_MIGRATION=false")
	driver, err := postgres.WithInstance(db, &postgres.Config{})
	if err != nil {
		return err
	}

	dir, err := filepath.Abs("../packages/db/migrations")
	if err != nil {
		return err
	}

	m, err := migrate.NewWithDatabaseInstance(fmt.Sprintf("file://%s", dir), dbName, driver)
	if err != nil {
		return err
	}

	if err := m.Up(); err != nil && err != migrate.ErrNoChange {
		return err
	}

	return nil
}
