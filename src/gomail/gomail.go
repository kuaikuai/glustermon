package gomail

import (
	"fmt"
	"net/smtp"
	"strings"
)

var GlobalSender Sender

type Sender struct {
	host        string
	server_addr string
	from        string
	passwd      string
}

type Email struct {
	to      string "to"
	subject string "subject"
	msg     string "msg"
}

func SetSender(host, server_addr, from, passwd string) {
	GlobalSender.host = host
	GlobalSender.server_addr = server_addr
	GlobalSender.from = from
	GlobalSender.passwd = passwd
}

func NewEmail(to, subject, msg string) *Email {
	return &Email{to: to, subject: subject, msg: msg}
}

func SendEmail(email *Email) error {
	auth := smtp.PlainAuth("", GlobalSender.from, GlobalSender.passwd, GlobalSender.host)
	sendTo := strings.Split(email.to, ";")
	fmt.Println("Count of sendTo:", len(sendTo))
	done := make(chan error, 1024)

	go func() {
		defer close(done)
		for _, v := range sendTo {
			str := strings.Replace("From: "+GlobalSender.from+"~To:"+v+"~Subject:"+email.subject+"~~", "~", "\r\n", -1) + email.msg

			err := smtp.SendMail(
				GlobalSender.server_addr,
				auth,
				GlobalSender.from,
				[]string{v},
				[]byte(str),
			)
			done <- err
			if err != nil {
				fmt.Println(err.Error())
			}
			fmt.Println("Send well")
		}
	}()
	for i := 0; i < len(sendTo); i++ {
		<-done
	}
	return nil
}
