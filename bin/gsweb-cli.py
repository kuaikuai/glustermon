#!/bin/python
import argparse, os, json

def debug_print(to_print, debug=True):
	if debug:
		print(to_print)

def robust_exec(cmds, get_output = False, verbose = True):
    """A function to execute a command locally. Because this function will run
    the command natively, the command will not be logged in the zrpc system.
    Consequently, the computing resource of the worker machine cannnot be holded.
    Therefore, this function can only be used to call some very lightweighted
    command such as a script coordinating complicated computation.

    Moreover, this function is used because in Linux, there is some unexpected behavior
    in using SIGINT to kill a subprocess with Python 2.x. More investigations are needed
    for Python 3.

    Args:
        cmds: A list of command-line arguments or a string of command line command.
              e.g. ['del', 'file2'] or 'del file2'. The former form is recommanded
        get_output: if True the stdout will be returned
        verbose: if True the cmds will be printed

    Returns:
        0 for no error. Otherwise, non-zero value for an error code
        (output_text, result) if get_output is True

    Raises:
        No exception
    """
    import platform, os, time, inspect, subprocess, shlex
    src_file_name = os.path.basename(inspect.getfile(inspect.currentframe()))
    if platform.system() == 'Linux':
        if os.environ.get('LD_LIBRARY_PATH'):
            # fucking bugs http://stackoverflow.com/questions/24788292/intermittent-oserror-errno-7-argument-list-too-long-with-short-command-12
            current_path = os.path.dirname(os.path.abspath(os.sys.argv[0]))
            if len(os.environ['LD_LIBRARY_PATH']) > 0:
                path_set = set(os.environ['LD_LIBRARY_PATH'].split(':'))
                if current_path not in path_set:
                    os.environ['LD_LIBRARY_PATH'] += ":" + current_path
            else:
                os.environ['LD_LIBRARY_PATH'] += ":" + current_path
        else:
            os.environ['LD_LIBRARY_PATH'] = os.path.dirname(os.path.abspath(os.sys.argv[0]))
#        print(os.path.dirname(os.sys.argv[0]))
        os.umask(002)

    if type(cmds) == str:
        if verbose:
            print(cmds)
        p = None
        if get_output:
            p = subprocess.Popen(shlex.split(cmds.encode('string-escape')), env=os.environ, stdout=subprocess.PIPE)
        else:
            p = subprocess.Popen(shlex.split(cmds.encode('string-escape')), env=os.environ)
        try:
            if get_output:
                (output_text, stderrdata) = p.communicate()
                return (output_text, p.returncode)
            else:
                p.communicate()
                return p.returncode
        except:
            print('[{0}] exception in robust_exec()'.format(src_file_name))
            if platform.system() == 'Linux':
                p.send_signal(2)
            else:
                p.kill()
            while p.poll() == None:
                print('[{0}] waiting the child exit'.format(src_file_name))
                time.sleep(0.05)
                pass
            exit(1)
    else:
        cmds = [str(cmd) for cmd in cmds]
        if verbose:
            print(' '.join(cmds))
        p = None
        if get_output:
            p = subprocess.Popen(cmds, env=os.environ, stdout=subprocess.PIPE)
        else:
            p = subprocess.Popen(cmds, env=os.environ)
        try:
            if get_output:
                (output_text, stderrdata) = p.communicate()
                return (output_text, p.returncode)
            else:
                p.communicate()
                return p.returncode
        except:
            print('[{0}] exception in robust_exec()'.format(src_file_name))
            if platform.system() == 'Linux':
                p.send_signal(2)
            else:
                p.kill()
            while p.poll() == None:
                print('[{0}] waiting the child exit'.format(src_file_name))
                time.sleep(0.05)
                pass
            exit(1)

def check_file_exist(filename):
	res = robust_exec(["test", "-e", filename])
	return res == 0

def current_user():
    (user_out, res) = robust_exec(['id', '-un'], get_output = True)
    if res == 0:
        return user_out.strip()
    return None

def get_gsweb_status():
	cmds = ['systemctl', 'status', 'gswebd']
	(out, res) = robust_exec(cmds, get_output=True)
	return res == 0

def stop_gsweb():
	print("Stop gswebd if it is running")
	cmds = ['systemctl', 'stop', 'gswebd']
	debug_print(cmds, debug)
	robust_exec(cmds, get_output = True)


def check_firewalld_runnning():
    cmds = ['pgrep', 'firewalld']
    (out, res) = robust_exec(cmds, get_output = True)
    return res == 0

def check_firewalld_installed():
    cmds = ['bash', '-c', 'yum list installed | grep firewalld']
    (out, res) = robust_exec(cmds, get_output = True)
    return res == 0

def setup_firewalld_options(debug=True):
    print("Setup firewalld options")
    if not check_firewalld_installed():
        #install firewalld
        robust_exec(["yum", "install", "-y", "firewalld"])
    else:
        debug_print("#####firewalld installed already#####",debug)
    if not check_firewalld_runnning():
        robust_exec(["systemctl", "restart", "firewalld"])
        robust_exec(["systemctl", "enable", "firewalld"])
    else:
        debug_print("#####firewalld is already running#####", debug)
    #### open port
    robust_exec(["bash", "-c", "firewall-cmd --zone=public --add-port=5555/tcp --permanent"])
    robust_exec(["bash", "-c", "firewall-cmd --reload"])

def generate_gswebd_service(install_path):
	print("#####generate gswebd service#####")
	service_string = "[Unit]" + "\n"
	service_string = service_string + "Description=gluster web"
	service_string = service_string + "\n"
	service_string = service_string + "[Service]\n"
	service_string = service_string + "Environment=\"TERM=xterm-256color\"\n"
	service_string = service_string + "ExecStart=" + install_path + "gsweb/bin/gswebd\n"
	service_string = service_string + "User=root\n"
	service_string = service_string + "Group=root\n"
	service_string = service_string + "UMask=002\n"
	service_string = service_string + "\n"
	service_string = service_string + "[Install]\n"
	service_string = service_string + "WantedBy=default.target\n"
	with open("gswebd.service", "w") as f:
		f.write(service_string)
	robust_exec(["cp", "-r", "gswebd.service", "/etc/systemd/system/gswebd.service"])
	os.remove("gswebd.service")

def install_gsweb(from_email, passwd, to_email, ip, install_path, host, server_addr, debug = True):
	public_list = ["css", "js", "template"]
	cu = current_user()
	if cu!='root':
		print('Please run this command as root')
		return
	# deal with the '/' of install_path
	if install_path[-1] != '/':
		install_path = install_path + "/"
    #### ensure gsweb is stoppped
	if get_gsweb_status():
		stop_gsweb()
    ##### copy gsweb files
    #mkdir gsweb directory
	debug_print("#####mkdir gsweb directory#####", debug)
	if not check_file_exist(install_path + "gsweb"):
		robust_exec(["mkdir", "-p", install_path + "gsweb"])
	else:
		print("#####{0}gsweb exists already#####".format(install_path))
    #copy gsweb bin files
	debug_print("#####copy gsweb bin files#####", debug)
	if not check_file_exist(install_path + "gsweb/bin"):
		robust_exec(["mkdir", "-p", install_path + "gsweb/bin"])
	robust_exec(["cp", "-r", "gswebd", install_path + "gsweb/bin/"])
	robust_exec(["cp", "-r", "gsweb-cli.py", install_path + "gsweb/bin/"])
	#change gswebd execute permission
	debug_print("#####change gswebd execute permission#####", debug)
	robust_exec(["chmod", "u+x", install_path + "gsweb/bin/gswebd"])
	#copy gsweb public files
	debug_print("#####copy gsweb public files#####", debug)
	if not check_file_exist(install_path + "gsweb/public"):
		robust_exec(["mkdir", "-p", install_path + "gsweb/public"])
	robust_exec(["mkdir", "-p", install_path + "gsweb/public/vol"])
	robust_exec(["mkdir", "-p", install_path + "gsweb/public/log"])
	for pub in public_list:
		debug_print("#####copy {0}#####".format(pub), debug)
		robust_exec(["cp", "-r", "../public/"+pub, install_path + "gsweb/public/"])
	#### setup firewall options
	setup_firewalld_options()
	### start gswebd service
	#generate config file
	debug_print("#####generate config file#####", debug)
	gswebdict = {
	"StaticDir": install_path + "gsweb/public",
	"IP": ip,
	"Port": "5555",
	"Host": host,
	"Server_addr": server_addr,
	"From": from_email,
	"Passwd": passwd,
	"To": to_email
	}
	gswebj = json.dumps(gswebdict, indent=1)
	with open("tmp.conf", "w") as f:
		debug_print(gswebj, debug)
		f.write(gswebj)
	robust_exec(["cp", "-r", "tmp.conf", install_path + "gsweb/bin/gswebd.conf"])
	os.remove("tmp.conf")
	#generate gswebd service
	generate_gswebd_service(install_path)
	#reload systemd
	debug_print("#####reload systemd#####", debug)
	robust_exec(["systemctl", "daemon-reload"])
	#enable and run gswebd service
	debug_print("#####enable and run gswebd service#####", debug)
	robust_exec(["systemctl", "restart", "gswebd"])
	robust_exec(["systemctl", "enable", "gswebd"])



if __name__ == "__main__":
	parser = argparse.ArgumentParser(prog='gsweb-cli.py', description = 'a helper cli for gluster-web')
	subparser = parser.add_subparsers()

	install_parser = subparser.add_parser('install', help = 'install gluster-web service')
	install_parser.add_argument('from_email', help='The mailbox to send the alarm email')
	install_parser.add_argument('passwd', help="To validate the sender's certificate")
	install_parser.add_argument('to_email', help='The mailbox to receive the alarm email')
	install_parser.add_argument('--ip', default='', help = 'LAN IP address of current machine')
	install_parser.add_argument('--install_path', default='/var', help='Where the gluster-web will be installed')
	install_parser.add_argument('--host', default='smtp.gmail.com', help='Host is used by PlainAuth to validate the TLS certificate')
	install_parser.add_argument('--server_addr', default='smtp.gmail.com:587', help='Smtp server address and related port')
	install_parser.set_defaults(debug=False)
	install_parser.set_defaults(func=lambda args: install_gsweb(args.from_email, args.passwd, args.to_email, args.ip, 
		args.install_path, args.host, args.server_addr, debug = args.debug))
	args = parser.parse_args()
	args.func(args)