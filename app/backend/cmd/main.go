package main

import (
	"backend/packages/api"
	"backend/packages/config"
)

func main() {
	config.InitConfig()
	api.StartServer()
}
