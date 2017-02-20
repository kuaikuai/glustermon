package main

import (
	"bufio"
	"fmt"
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
		execError = err
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
			execError = err
			log.Println(err.Error())
			return
		}
		volError = fmt.Errorf("Error: Too many entries to be healed")
		log.Println(volError.Error())
		return
	case err := <-done:
		if err != nil {
			execError = err
			log.Println(err.Error())
			return
		}
		if bricks, volError = parseVolumeFile(volumeFilePath); volError != nil {
			return nil, nil, volError
		}
		return
	}
}

func DeleteEntries(brick)
