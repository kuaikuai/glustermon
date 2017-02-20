package main

import (
	"encoding/json"
	"fmt"
	"html/template"
	"log"
	"net/http"
	"os"
	"path/filepath"
)

var currentVolumeFiles []*os.File

type RequsetDeleteBrick struct {
	VolInCheck string
	BrickName  string
}

type GlusterContent struct {
	Vols []string
}

type VolumeContent struct {
	Vols       []string
	VolInCheck string
	Bricks     []*Brick
}

func brickDeleteHandler(rw http.ResponseWriter, req *http.Request) {
	var rdb RequsetDeleteBrick
	decoder := json.NewDecoder(req.Body)
	if err := decoder.Decode(&rdb); err != nil {
		log.Println(err.Error())
	}
	vol := rdb.VolInCheck
	brickName := rdb.BrickName

}

func volumeHandler(rw http.ResponseWriter, req *http.Request) {
	// var rb RequsetBody
	// decoder := json.NewDecoder(req.Body)
	// if err := decoder.Decode(&rb); err != nil {
	// 	log.Println(err.Error())
	// }
	// vol := rb.Vol
	req.ParseForm()
	vol := req.Form.Get("vol")
	fmt.Println("Vol in volumeHandler:", vol)
	bricks, execError, volError := GetVolumeDetail(vol)
	if execError != nil {
		log.Println("Error: GetVolumeDetail ", execError.Error())
	}
	if volError != nil {
		log.Println("Error: GetVolumeDetail ", volError.Error())
	}
	for _, brick := range bricks {
		log.Println(*brick)
	}
	volumes, err := GetVolumes()
	if err != nil {
		log.Println(err.Error())
	}
	// rw.Write([]byte(GenerateHTML(bricks)))
	content := &VolumeContent{
		Vols:       volumes,
		VolInCheck: vol,
		Bricks:     bricks,
	}
	staticDir := GetConfig().StaticDir
	t := template.Must(template.ParseFiles(
		filepath.Join(staticDir, "template/header.html"),
		filepath.Join(staticDir, "template/footer.html"),
		filepath.Join(staticDir, "template/volume.html")))
	t.ExecuteTemplate(rw, "volume", content)
}

func glusterHandler(rw http.ResponseWriter, req *http.Request) {
	volumes, err := GetVolumes()
	if err != nil {
		log.Println(err.Error())
	}
	log.Println("volumes:", volumes)
	content := &GlusterContent{
		Vols: volumes,
	}
	staticDir := GetConfig().StaticDir
	t := template.Must(template.ParseFiles(
		filepath.Join(staticDir, "template/header.html"),
		filepath.Join(staticDir, "template/footer.html"),
		filepath.Join(staticDir, "template/index.html")))
	t.ExecuteTemplate(rw, "index", content)

}

func main() {
	config := LoadConfig()
	logDir := filepath.Join(config.StaticDir, "log")
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
	fs := http.FileServer(http.Dir(config.StaticDir))
	http.Handle("/public/", http.StripPrefix("/public/", fs))
	http.HandleFunc("/index", glusterHandler)
	http.HandleFunc("/volume/detail", volumeHandler)
	http.HandleFunc("/brick/delete", brickDeleteHandler)
	go http.ListenAndServe("127.0.0.1:"+config.Port, nil)
	if err := http.ListenAndServe(config.IP+":"+config.Port, nil); err != nil {
		log.Fatal("Error: ListenAndServe", config.Port)
	}
}
