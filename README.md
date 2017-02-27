# glustermon
A tool to monitor the running of [GlusterFS](https://www.gluster.org/) and report if [GlusterFS](https://www.gluster.org/) encounters a problem


## Overview
`GlusterFS` is a scalable network filesystem. However, if the `GlusterFS` encounters a problem, such as:
* `brick` offline
* machine crash
* `Split-brain` files
* Too many files to heal

We should find the problem as soon as possible and take actions to take `GlusterFS` back to normal.
Our glustermon will monitor the running of `GlusterFS` and report the problem by sending an alert email when necessary.


## Install
You have to dowaload the source code, build it and install it step by step.

### Download

* Install [Golang](https://golang.org/)
* Download the source code with the command, replace the `username` with yours:
```
git clone https://bitbucket.org/<username>/glustermon.git
```

* Enter the `glustermon` directory, and set your `GOPATH` :
```
cd glustermon
export GOPATH=`pwd`
```

### Build
* In the `glustermon` directory, build the source code:
```
make
```

### Install
* Enter the `bin` directory
```
cd bin/
```

* Lauch the install process with `python` script, you have to pass the `address` and `passwd` of the alert email sender and `address` of the alert email receiver: 
```
python gsweb-cli.py install <from_email> <passwd> <to_email>
```

## Start and Stop
`glustermon` will run as a linux system daemon.

You can start/stop it with the commands below:
```
sudo systemctl start/stop gswebd
```


## Tips

What I want to talk about here are some tips about the `address` and `passwd` of the alert email sender. I will take [gmail](https://mail.google.com/mail) for example.

You can surely pass `PASSWD` in `python` script above. However, it's unsafe.

Instead, you can set an [App password](https://support.google.com/accounts/answer/185833) and replace the `PASSWD` above with it:

* Step1: Turn on your [2-step verification](https://support.google.com/accounts/answer/185839)
* Step2: Generate your 16-bit `App passwords`, and pass the `PASSWD` with it.

## License 
MIT (see [LICENSE](https://github.com/orcaman/concurrent-map/blob/master/LICENSE) file)