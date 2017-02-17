package main

import (
	"fmt"
	"log"
	"os"
	"path/filepath"
	"time"
)

func SetLog(logDir string) (*os.File, error) {
	logName := fmt.Sprintf("%s.log", time.Now().Format("01-02:15:04:05"))
	logPath := filepath.Join(logDir, logName)
	logFile, err := os.Create(logPath)
	if err != nil {
		log.Print("Error: open file", err)
		return nil, err
	}
	log.SetOutput(logFile)
	return logFile, nil
}

//RotateLog creates a new log file when the current log file is too bigger
func RotateLog(logDir string, oldLogFile *os.File) {
	for {
		fileInfo, err := oldLogFile.Stat()
		if err != nil {
			log.Fatalf("Error: file stat: %s \n", oldLogFile.Name())
		}
		if fileInfo.Size() > 1024*1024*200 {
			newLogName := fmt.Sprintf("%s.log", time.Now().Format("01-02:15:04:05"))
			newLogPath := filepath.Join(logDir, newLogName)
			newLogFile, err := os.Create(newLogPath)
			if err != nil {
				log.Fatalf("Error: open file %s \n", newLogPath)
			}
			log.SetOutput(newLogFile)
			go RotateLog(logDir, newLogFile)
			return
		}
		time.Sleep(time.Minute * 1)
	}
}
