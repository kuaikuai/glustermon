package main

import (
	"fmt"
	"log"
	"os"
	"path"
)

func main() {
	config := LoadConfig()
	logDir := path.Join(config.StaticDir, "log")
	exist, err := PathExists(logDir)
	if err != nil {
		log.Fatalln("Error: check log path")
	}
	if !exist {
		os.Mkdir(logDir, 744)
	}
	logFile, err := SetLog(logDir)
	if err != nil {
		os.Exit(-1)
	}
	go RotateLog(logDir, logFile)
	volumes, err := GetVolumes()
	if err != nil {
		log.Println(err.Error())
	}
	fmt.Println(volumes)
}
