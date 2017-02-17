package main

import (
	"io/ioutil"
	"log"
	"os"
	"testing"
	"time"
)

func TestLog(t *testing.T) {
	logDir := "/tmp/test_log"
	exist, err := PathExists(logDir)
	if err != nil {
		t.Errorf("PathExists(%s)", logDir)
	}
	if !exist {
		os.Mkdir(logDir, 0744)
	}
	logFile, err := SetLog(logDir)
	if err != nil {
		t.Error("Set Log")
	}
	go RotateLog(logDir, logFile)
	go func() {
		for {
			log.Println(time.Now().String())
		}
	}()
	time.Sleep(time.Minute * 1)
	time.Sleep(time.Second * 1) //Ensure the check of rotatelog
	files, _ := ioutil.ReadDir(logDir)
	if len(files) <= 1 {
		t.Errorf("Log cannot work right")
	}
	os.RemoveAll(logDir)
}

func TestGetVolumes(t *testing.T) {

}
