package main

import (
	"fmt"
	// "io/ioutil"
	// "log"
	"os"
	"testing"
	// "time"
)

// func TestLog(t *testing.T) {
// 	logDir := "/tmp/test_log"
// 	exist, err := PathExists(logDir)
// 	if err != nil {
// 		t.Errorf("PathExists(%s)", logDir)
// 	}
// 	if !exist {
// 		os.Mkdir(logDir, 0744)
// 	}
// 	logFile, err := SetLog(logDir)
// 	if err != nil {
// 		t.Error("Set Log")
// 	}
// 	go RotateLog(logDir, logFile)
// 	go func() {
// 		for {
// 			log.Println(time.Now().String())
// 		}
// 	}()
// 	time.Sleep(time.Minute * 1)
// 	time.Sleep(time.Second * 1) //Ensure the check of rotatelog
// 	files, _ := ioutil.ReadDir(logDir)
// 	if len(files) <= 1 {
// 		t.Errorf("Log cannot work right")
// 	}
// 	os.RemoveAll(logDir)
// }

func TestGetVolumes(t *testing.T) {
	LoadConfig()
	volDir := "/tmp/test_vol"
	exist, err := PathExists(volDir)
	if err != nil {
		t.Errorf("PathExists(%s)", volDir)
	}
	if !exist {
		os.Mkdir(volDir, 0744)
	}
	bricks, execError, volError := GetVolumeDetail("gv3")
	if execError != nil {
		t.Errorf(execError.Error())
	}
	if volError != nil {
		t.Errorf(volError.Error())
	}
	for _, brick := range bricks {
		fmt.Println(*brick)
	}
}
