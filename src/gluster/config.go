package main

import (
	"encoding/json"
	"log"
	"os"
)

type Config struct {
	StaticDir string
}

var config *Config

func LoadConfig() *Config {
	file, err := os.Open("/var/gluster_web/bin/glfs.config")
	if err != nil {
		log.Fatalf("Error: Open config file glfs.config %v\n", err.Error())
	}
	config = &Config{}
	decoder := json.NewDecoder(file)
	if err := decoder.Decode(config); err != nil {
		log.Fatalf("Error: decode config from reader %v\n", err)
	}
	return config
}

func GetConfig() *Config {
	if config == nil {
		log.Fatalf("Error: config file not loaded")
	}
	return config
}
