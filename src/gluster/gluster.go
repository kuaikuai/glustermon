package main

import (
	"os/exec"
	"strings"
)

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
