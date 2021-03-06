package main

import (
	"fmt"
	"log"
	"sync"
	"time"

	"gomail"
)

const (
	SUBJECT = "Gluster Error"
)

func sendAlarmEmail(to, subject, msg string) error {
	email := gomail.NewEmail(to, subject, msg)
	return gomail.SendEmail(email)
}

func updateVolumesInWatch(volumes *[]string) {
	for {
		currentVols, err := GetVolumes()
		if err != nil {
			log.Println("Error:", err.Error())
			return
		}
		volumes = &currentVols
		time.Sleep(time.Hour * 1)
	}
}

func watchVolumes() {
	var volsInWatch *[]string
	currentVols, err := GetVolumes()
	if err != nil {
		log.Println("Error:", err.Error())
		return
	}
	volsInWatch = &currentVols
	go updateVolumesInWatch(volsInWatch)
	config := GetConfig()
	to := config.To
	for {
		var wg sync.WaitGroup
		for _, vol := range *volsInWatch {
			wg.Add(1)
			go func(volume string) {
				defer wg.Done()
				defer fmt.Printf("Volume %s finish watch\n", volume)
				for {
					bricks, execError, volError := GetVolumeDetail(volume)
					if execError != nil {
						log.Println("Error: GetVolumeDetail ", execError.Error())
						sendAlarmEmail(to, SUBJECT, execError.Error())
					}
					if volError != nil {
						log.Println("Error: GetVolumeDetail ", volError.Error())
						sendAlarmEmail(to, SUBJECT, volError.Error())
					}
					for _, brick := range bricks {
						if brickStatus, ok := checkBrick(volume, brick); !ok {
							sendAlarmEmail(to, SUBJECT, brickStatus)
						}
					}
					time.Sleep(time.Minute * 10)
					return
				}
			}(vol)
		}
		wg.Wait() //Wait for all the routines' stop, and start new watch
	}
}
