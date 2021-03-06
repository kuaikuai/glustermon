package main

import (
	"bufio"
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"time"
)

type Brick struct {
	Name            string
	Status          string
	HealCount       int
	SplitBrainCount int
}

func checkBrick(vol string, brick *Brick) (string, bool) {
	if brick.Status != "Connected" {
		brickStatus := fmt.Sprintf("Error of brick %s in Volume %s, status: %s\n", brick.Name, vol, brick.Status)
		log.Println(brickStatus)
		return brickStatus, false
	} else if brick.HealCount > 0 {
		brickStatus := fmt.Sprintf("Error of brick %s in Volume %s, healcount: %d\n", brick.Name, vol, brick.HealCount)
		log.Println(brickStatus)
		return brickStatus, false
	} else if brick.SplitBrainCount > 0 {
		brickStatus := fmt.Sprintf("Error of brick %s in volume %s, splitbraincount: %d\n", brick.Name, vol, brick.SplitBrainCount)
		log.Println(brickStatus)
		return brickStatus, false
	} else {
		return "", true
	}
}

func GetVolumes() ([]string, error) {
	cmds := exec.Command("gluster", "volume", "info")
	out, err := cmds.Output()
	if err != nil {
		return nil, err
	}
	lines := strings.Split(string(out), "\n")
	var volumes []string
	for _, line := range lines {
		if strings.Contains(line, "Volume Name:") {
			vol := strings.TrimSpace(strings.Split(line, ":")[1])
			volumes = append(volumes, vol)
		}
	}
	return volumes, nil
}

func parseVolumeFile(volumeFilePath string) ([]*Brick, error) {
	var bricks []*Brick
	tmpBrick := new(Brick)
	splitBrainCount := 0
	file, err := os.Open(volumeFilePath)
	if err != nil {
		log.Println(err.Error())
		return nil, err
	}
	defer file.Close()
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := scanner.Text()
		if strings.Contains(line, "Brick") && strings.Contains(line, ":/") {
			tmpBrick.Name = strings.SplitN(line, " ", 2)[1]
		}
		if strings.Contains(line, "Is in split-brain") {
			splitBrainCount++
		}
		if strings.Contains(line, "Status:") {
			tmpBrick.Status = strings.TrimSpace(strings.SplitN(line, ":", 2)[1])
		}
		if strings.Contains(line, "Number of entries:") {
			tmpBrick.HealCount, _ = strconv.Atoi(strings.TrimSpace(strings.Split(line, ":")[1]))
			tmpBrick.SplitBrainCount = splitBrainCount
			bricks = append(bricks, tmpBrick)
			splitBrainCount = 0
			tmpBrick = new(Brick)
		}
	}
	if err := scanner.Err(); err != nil {
		log.Println(err.Error())
		return nil, err
	}
	return bricks, nil
}

func GetVolumeDetail(vol string) (bricks []*Brick, execError, volError error) {
	bricks = nil
	execError = nil
	volError = nil
	staticDir := GetConfig().StaticDir
	volumeFileName := fmt.Sprintf("vol_%s_%s.txt", vol, time.Now().Format("01-02:15:04:05"))
	volumeFilePath := filepath.Join(staticDir, "vol", volumeFileName)
	cmds := exec.Command("bash", "-c", "gluster volume heal "+vol+" info > "+volumeFilePath)
	// log.Println(cmds.Args)
	if err := cmds.Start(); err != nil {
		execError = fmt.Errorf("Volume %s Error: %s\n", vol, err.Error())
		log.Println(err.Error())
		return
	}
	done := make(chan error, 1)
	go func() {
		done <- cmds.Wait()
	}()
	select {
	case <-time.After(30 * time.Minute): //Too many entries to heal
		if err := cmds.Process.Kill(); err != nil {
			execError = fmt.Errorf("Volume %s Error: %s\n", vol, err.Error())
			log.Println(execError.Error())
			return
		}
		volError = fmt.Errorf("Error: Too many entries to be healed")
		log.Println(volError.Error())
		return
	case err := <-done:
		if err != nil {
			execError = fmt.Errorf("Volume %s Error: %s\n", vol, err.Error())
			log.Println(execError.Error())
			return
		}
		if bricks, volError = parseVolumeFile(volumeFilePath); volError != nil {
			volError = fmt.Errorf("Volume %s Error: %s\n", vol, volError.Error())
			return nil, nil, volError
		}
		return
	}
}

//Remove volfile generated a week ago in case the vol directory is too large
func RemoveVolFile(volDir string) {
	tick := time.Tick(24 * time.Hour)
	for _ = range tick {
		files, err := ioutil.ReadDir(volDir)
		if err != nil {
			log.Print("Read vol directory info error", err)
			return
		}
		dayDuration, _ := time.ParseDuration("-24h")
		timeWeekAgo := time.Now().Add(7 * dayDuration)
		for _, file := range files {
			if file.ModTime().Before(timeWeekAgo) {
				err := os.Remove(filepath.Join(volDir, file.Name()))
				if err != nil {
					log.Print("Error: remove volfile", err)
				}
			}
		}
	}
}
