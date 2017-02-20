package main

import (
	"fmt"
	"html/template"
	"os"
	"strings"
)

func PathExists(path string) (bool, error) {
	_, err := os.Stat(path)
	if err == nil {
		return true, nil
	}
	if os.IsNotExist(err) {
		return false, nil
	}
	return false, err
}

func GenerateHTML(bricks []*Brick) template.HTML {
	var out []string
	for _, brick := range bricks {
		if brick.Status == "Connected" {
			msg := fmt.Sprintf("Brick %s; Status: %s; healCount:%d; splitBrainCount:%d\n", brick.Name, brick.Status, brick.HealCount, brick.SplitBrainCount)
			out = append(out, msg)
		} else {
			msg := fmt.Sprintf("Brick %s; Status: %s\n", brick.Name, brick.Status)
			out = append(out, msg)
		}
	}
	return template.HTML(strings.Join(out, "<br/>"))
}
