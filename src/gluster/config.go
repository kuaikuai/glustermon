package main

import (
	"encoding/json"
	"log"
	"os"
)

type Config struct {
	StaticDir   string
	IP          string
	Port        string
	Host        string
	Server_addr string
	From        string
	Passwd      string
	To          string
}

var config *Config

func LoadConfig() *Config {
	file, err := os.Open("/var/glustermon/bin/glustermond.conf")
	if err != nil {
		log.Fatalf("Error: Open config file glustermond.conf %v\n", err.Error())
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
