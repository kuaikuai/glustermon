import argparse, os, shutil, subprocess, multiprocessing, urllib2

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

def install_epel():
	rpm_url = "https://dl.fedoraproject.org/pub/epel/7/x86_64/e/epel-release-7-9.noarch.rpm"
	cmds = ['wget', rpm_url, '-O', '/tmp/epel-release-7-9.noarch.rpm']
	if robust_exec(cmds) != 0:
		print('Error in downloading epel.rpm')
		exit(-1)
	cmds = ['sudo', 'rpm', '-ivh', '--replacepkgs', '/tmp/epel-release-7-9.noarch.rpm']
	if robust_exec(cmds) != 0:
		print('Error in installing epel.rpm')
		exit(-1)
	os.remove('/tmp/epel-release-7-9.noarch.rpm')

def map_func(func_name, args_list, thread_per_cmd = 1, cpu_num = 0, gpu = False):
    """A function to map a list of command-line commands
    to the local machine according to cpu_num

    Args:
        func_name:  The function to be map. The function takes a single argument
        args_list: A list of arguments. Each command is also in the form
              of a list of arguments. e.g. [['del', 'file1'],['del', 'file2']]
              The arguments can be of non-string simple type. This function will
              automatically handle the type conversion.
        thread_per_cmd: Specify the number of threads each command occupies. A value
              smaller than 1 will indicate each command will take over all the
              cores of the local machine.
        cpu_num: Indicate the number of CPUs of the local machine. If this argument is
                 set to 0, then for local execution, the number of cores will be
                 set as cpu_num.
        gpu: Useless flag for local map

    Returns:
        No return value

    Raises:
        No exception
    """
    if len(args_list) == 0: return

    if thread_per_cmd <= 0:
        thread_per_cmd = multiprocessing.cpu_count()

    if cpu_num == 0:
        cpu_num = multiprocessing.cpu_count()

    process_num = cpu_num / thread_per_cmd

    process_num = min(process_num, len(args_list))
    process_num = max(process_num, 1)

    print('Process #: {0}'.format(process_num))

    if (process_num > 1):
        threadPool = multiprocessing.Pool(processes = process_num)
        p = threadPool.map_async(func_name, iterable = args_list, chunksize = 1)
        try:
            results = p.get(0xFFFFFFFF)
        except KeyboardInterrupt:
            print('parent received control-c')
            threadPool.terminate()
            threadPool.join()
            exit(1)
    else:
        for args_item in args_list:
            func_name(args_item)

def map_local(cmds, thread_per_cmd = 1, cpu_num = 0, gpu = False):
    """A function to map a list of command-line commands
    to the local machine according to cpu_num

    Args:
        cmds: A list of command-line commands. Each command is also in the form
              of a list of arguments. e.g. [['del', 'file1'],['del', 'file2']]
              The arguments can be of non-string simple type. This function will
              automatically handle the type conversion.
        thread_per_cmd: Specify the number of threads each command occupies. A value
              smaller than 1 will indicate each command will take over all the
              cores of the local machine.
        cpu_num: Indicate the number of CPUs of the local machine. If this argument is
                 set to 0, then for local execution, the number of cores will be
                 set as cpu_num.
        gpu: Useless flag for local map

    Returns:
        No return value

    Raises:
        No exception
    """
    map_func(robust_exec, cmds, thread_per_cmd = thread_per_cmd, cpu_num = cpu_num, gpu = gpu)

def firewall(max_brick_num):
    '''
    enable firewall according to this article
    http://www.gluster.org/community/documentation/index.php/Basic_Gluster_Troubleshooting
    '''
    ports = ['--add-port=24007-24008/tcp' # enable firewall for Trusted Pool/Deamon and infiniband manangerment
            , '--add-port=24009-{0}/tcp'.format(24009+max_brick_num)
            , '--add-port=49152-{0}/tcp'.format(49152+max_brick_num)
            , '--add-port=2409/tcp' # port mapping
            , '--add-port=111/tcp' # port mapping
            # enable firewall for glusterfs/nfs/cifs clients
            , '--add-port=139/tcp'
            , '--add-port=445/tcp'
            , '--add-port=965/tcp'
            , '--add-port=2049/tcp'
            , '--add-port=38465-38469/tcp'
            , '--add-port=111/udp'
            , '--add-port=963/udp'
            , '--add-service=nfs'
            , '--add-service=samba'
            , '--add-service=samba-client'
            ]

    for port in ports:
        cmds = ['sudo', 'firewall-cmd', '--zone=public', port, '--permanent']
        if robust_exec(cmds) != 0:
            print('Error in setting firewall rules')
            exit(-1)

    cmds = ['sudo', 'firewall-cmd', '--reload']
    if robust_exec(cmds) != 0:
        print('Error in setting firewall rules')
        exit(-1)

def replace_string_in_file(file_src, file_dest, src, target):
	lines = []
	with open(file_src) as infile:
		for line in infile:
			line = line.replace(src, target)
			lines.append(line)
	with open(file_dest, 'w') as outfile:
		for line in lines:
			outfile.write(line)

def install(version = 'LATEST'):
    print('kill any yum process if any')
    cmds = ['sudo', 'pkill', '-f', 'yum']
    if robust_exec(cmds) != 0:
        print('Error in stopping yum')
        exit(-1)
    # install epel, specially for liburcu-cds.so and liburcu-bp.so
    install_epel()
    # install latest gluster3.7 All gluster should be the same version.
    cwd = os.path.dirname(os.path.abspath(os.sys.argv[0]))
    print('Current folder {0}'.format(cwd))
    repo_file = os.path.join(cwd, 'glusterfs-epel.repo')
    if not os.path.exists(repo_file):
        print('Cannot file the repo file: {0}'.format(repo_file))
        exit(-1)
    #Specify the glusterfs to install
    repo_file_new = os.path.join(cwd, 'glusterfs-epel.repo.gen')
    replace_string_in_file(repo_file, repo_file_new, 'LATEST', version)
    cmds = ['sudo', 'cp', repo_file_new, '/etc/yum.repos.d/glusterfs-epel.repo']
    if robust_exec(cmds) != 0:
        print('Error in copying repo')
        exit(-1)
    cmds = [['sudo', 'yum', 'install', '-y', 'glusterfs-server']
            , ['sudo', 'systemctl', 'start', 'glusterd']
            , ['sudo', 'systemctl', 'enable', 'glusterd']]
    for cmd in cmds:
        if robust_exec(cmd) != 0:
            print('Error in installing gluster')
            exit(-1)
    # install fuse
    cmd = ['sudo', 'yum', 'install', 'fuse', '-y']
    if robust_exec(cmd) != 0:
	print('Error in installing fuse')
	exit(-1)
    # the policy file handles the SELinux error in auditing
    policy_file = os.path.join(cwd, 'gluster_policy.pp')
    cmds = ['sudo', 'semodule', '-i', policy_file]
    if robust_exec(cmds) != 0:
        print('Error in granting the policy')
        exit(-1)

    policy_file = os.path.join(cwd, 'gluster_policy_2.pp')
    cmds = ['sudo', 'semodule', '-i', policy_file]
    if robust_exec(cmds) != 0:
        print('Error in granting the policy_2')
        exit(-1)

    firewall(200)

def mount(gluster_volume, mount_point, gluster_host = '127.0.0.1'):
    print('generate service to mount gluster volume {0}:/{1} to {2}'.format(gluster_host
        , gluster_volume, mount_point))
    cwd = os.path.dirname(os.path.abspath(os.sys.argv[0]))
    service_name = 'mount-mnt-{0}.service'.format(gluster_volume)
    tmp_service_file = os.path.join(cwd, service_name)
    with open(tmp_service_file, 'wb') as service_stream:
        print('------ Service unit content -----')
        service_stream.write('[Unit]\n')
        service_stream.write('Description=Mount a gluster volume\n')
        service_stream.write('After=glusterd.service\n')
        service_stream.write('Requires=glusterd.service\n')
        service_stream.write('\n')
        service_stream.write('[Service]\n')
        service_stream.write('Type=oneshot\n')
        service_stream.write('ExecStart=/usr/bin/mount -o acl -t glusterfs {0}:{1} {2}\n'.format(gluster_host, gluster_volume, mount_point))
        service_stream.write('ExecStop=/usr/bin/fusermount -uz {0}\n'.format(mount_point))
        service_stream.write('User=root\n')
        service_stream.write('RemainAfterExit=True\n')
        service_stream.write('\n')
        service_stream.write('[Install]\n')
        service_stream.write('WantedBy=default.target\n')

    if not os.path.exists(mount_point):
        cmds = ['sudo', 'mkdir', '-p', mount_point]
        if robust_exec(cmds) != 0:
            print('Cannot create the mount point at {0}'.format(mount_point))
            exit(-1)
    cmds = [['sudo', 'cp', '-f', tmp_service_file, '/etc/systemd/system']
            , ['sudo', 'chmod', '664', os.path.join('/etc/systemd/system', os.path.basename(tmp_service_file))]
            , ['sudo', 'systemctl', 'daemon-reload']
            , ['sudo', 'systemctl', 'enable', service_name]
            , ['sudo', 'systemctl', 'start', service_name]
            , ['sudo', 'systemctl', 'status', service_name]
            ]
    for cmd in cmds:
        if robust_exec(cmd) != 0:
            print('cmd error'.format(mount_point))
            exit(-1)

    if os.path.exists(tmp_service_file):
        os.remove(tmp_service_file)

def current_user():
    (user_out, res) = robust_exec(['id', '-un'], get_output = True)
    if res == 0:
        return user_out.strip()
    return None

def peers(remote_host = None):
    print('current user: '+current_user())
    cu = current_user()
    cmds = []
    if remote_host != None:
        cmds = ['ssh', '-t', remote_host]
        print('Type sudo password for {0}'.format(remote_host))
    cmds.extend(['sudo', 'gluster', 'peer', 'status'])
    (peers_out, res) = robust_exec(cmds, get_output = True)
    peer_infos = dict()
    if res != 0:
        return peer_infos

    peers_out = peers_out.split('\n')
    for i in range(0, len(peers_out)):
        line = peers_out[i]
        line = line.strip()
        if len(line) > 0:
            comps = line.split()
            if comps[0] == 'Hostname:':
                peer_info = dict()
                peer_info['hostname'] = comps[1].strip()
                uuid_line = peers_out[i+1]
                peer_info['uuid'] = uuid_line.split()[1].strip()
                state_line = peers_out[i+2].strip()
                peer_info['state'] = (state_line.find('Connected') >= 0)
                peer_infos[peer_info['hostname']] = peer_info

    return peer_infos

def volume_ls():
    volumes = []
    cmds = ['sudo', 'gluster', 'volume', 'info']
    (volume_out, res) = robust_exec(cmds, get_output = True)
    if res != 0:
        return volumes
    volume_out = volume_out.split('\n')
    for i in range(0, len(volume_out)):
        line =  volume_out[i].strip()
        if len(line) > 0 and line.find('Volume Name:') >= 0:
            volume_head_comps = line.split()
            if (len(volume_head_comps) == 3):
                volumes.append(volume_head_comps[2])
    return volumes

def brick_ls(volume = None, peer = None):
    if volume == None:
        brick_infos = dict()
        volumes = volume_ls()
        print(volumes)
        for volume in volumes:
            brick_infos[volume] = brick_ls(volume = volume, peer = peer)
        return brick_infos
    else:
        brick_infos = []
        cmds = ['sudo', 'gluster', 'volume', 'info', volume]
        (brick_out, res) = robust_exec(cmds, get_output = True)
        if res != 0:
            return brick_infos
        brick_out = brick_out.split('\n')
        volume_start = False
        brick_num = 0
        for i in range(0, len(brick_out)):
            line = brick_out[i].strip()
            if line.find('Volume Name:') >= 0:
                volume_name = line.split()[2]
                if volume_name == volume and not volume_start:
                    volume_start = True
                elif volume_name == volume and volume_start:
                    print('Error in parsing bricks')
                    exit(-1)
            elif line.find('Number of Bricks:') >= 0 and volume_start:
                comps = line.split()
                brick_num = int(comps[len(comps)-1])
                print('{0} bricks in {1}'.format(brick_num, volume))
            elif line.find('Bricks:') >= 0 and volume_start:
                for bi in range(0, brick_num):
                    brick_str = brick_out[i+bi+1].strip().split()[1]
                    if peer != None:
                        if brick_str.find(peer) >= 0:
                            brick_infos.append(brick_str.split(':')[1])
                    else:
                        brick_infos.append(brick_str)
                volume_start = False
        return brick_infos

def volume_peers_ls(volume):
    bricks = brick_ls(volume)
    peer_set = set()
    for brick in bricks:
        peer_set.add(brick.split(':')[0])

    if len(peer_set) > 0:
        return [x for x in peer_set]
    else:
        return []

def volume_status(volume):
    cmds = ['sudo', 'gluster', 'volume', 'status', volume]
    (volume_out, res) = robust_exec(cmds, get_output = True)

    volume_state = dict()
    if res:
        return volume_state
    volume_out = volume_out.split('\n')
    for i in range(0, len(volume_out)):
        line = volume_out[i].strip()
        if line.find('Brick') == 0:
            comps = line.split()
            if len(comps) == 6:
                brick_state = dict()
                brick_state['brick'] = comps[1]
                brick_state['tcp_port'] = comps[2]
                brick_state['rdma_port'] = comps[3]
                brick_state['online'] = (comps[4] == 'Y')
                brick_state['pid'] = comps[5]
                volume_state[brick_state['brick']] = brick_state

    return volume_state

def volume_mountpoints():
    cmds = ['mount', '-l']
    (out, res) = robust_exec(cmds, get_output = True)
    if res != 0:
        return None

    out = out.split('\n')
    volume_mount_points = []
    for line in out:
        line = line.strip()
        if line.find('glusterfs') >= 0:
            line = line.split()
            if len(line) > 2:
                volume_mp_info = dict()
                volume_mp_info['remote'] = ''
                volume_mp_info['volume'] = volume = line[0]
                volume_mp_info['mountpoint'] = line[2]
                volume = volume.split(':')
                if len(volume) > 1:
                    volume_mp_info['remote'] = volume[0]
                    volume_mp_info['volume'] = volume[1].lstrip('/')
                volume_mount_points.append(volume_mp_info)
    return volume_mount_points

def extract_volume_mountpoint(volume_path):
    vmps = volume_mountpoints()
    print(vmps)
    volume_path = os.path.abspath(volume_path)
    if vmps == None:
        return (None, None)
    for vmp in vmps:
        if volume_path.find(vmp['mountpoint']) >= 0:
            return (vmp['volume'], vmp['mountpoint'])
    return (None, None)

def status(volume):
    print(peers())
    volume_bricks = brick_ls(volume)
    volume_state = volume_status(volume)
    online_num = 0
    for brick in volume_bricks:
        if brick not in volume_state:
            print('Brick {0} may be offline'.format(brick))
        else:
            if not volume_state[brick]['online']:
                print('Brick {0} is offline'.format(brick))
            else:
                online_num += 1

    if online_num == len(volume_bricks):
        print('All bricks in {0} are online. SAFE!!!'.format(volume))
        return (True, online_num, len(volume_bricks))
    elif online_num < len(volume_bricks)*2/3:
        print('{0} bricks in {1} are not online! The filesystem may not work'.format(len(volume_bricks) - online_num, volume))
        return (False, online_num, len(volume_bricks))
    else:
        print('{0} bricks in {1} are not online! The filesystem should still work'.format(len(volume_bricks) - online_num, volume))
        return (False, online_num, len(volume_bricks))

def brick_to_hash_file_path(brick_path, brick_root):
    cmds = ['getfattr', '-d', '-m', 'gfid', '-e', 'hex', brick_path]
    out = None
    res = 0
    try:
        (out, res) = robust_exec(cmds, get_output = True, verbose = False)
    except OSError as e:
        print(cmds)
        exit(-1)

    if res != 0:
        return None

    out = out.split('\n')
    if len(out) < 2:
        return None

    hash_str = out[1].strip().replace('trusted.gfid=', '')
    if len(hash_str) < 34:
        return None

    if hash_str[0:2] != '0x':
        return None

    hash_com_1 = hash_str[2:4]
    hash_com_2 = hash_str[4:6]
    hash_com_3 = hash_str[6:10]
    hash_com_4 = hash_str[10:14]
    hash_com_5 = hash_str[14:18]
    hash_com_6 = hash_str[18:22]
    hash_com_7 = hash_str[22:34]

    hash_path = os.path.join(hash_com_1
                            , os.path.join(hash_com_2
                                , '{0}{1}{2}-{3}-{4}-{5}-{6}'.format(hash_com_1
                                                            , hash_com_2
                                                            , hash_com_3
                                                            , hash_com_4
                                                            , hash_com_5
                                                            , hash_com_6
                                                            , hash_com_7)))

    hash_root = os.path.join(brick_root, '.glusterfs')
    return os.path.join(hash_root, hash_path)

def remove_brick_dir(brick_dir, brick_root, debug = True):
    for item in os.listdir(brick_dir):
        brick_item = os.path.join(brick_dir, item)
        if os.path.isdir(brick_item):
            remove_brick_dir(brick_item, brick_root, debug = debug)
        else:
            remove_brick_file(brick_item, brick_root, debug = debug)
    if debug:
        print('[debug] remove {0}'.format(brick_dir))
    else:
        if os.path.exists(brick_dir):
            print('remove dir {0}'.format(brick_dir))
            os.rmdir(brick_dir)
        pass
    pass

def remove_brick_file(brick_file, brick_root, debug = True):
    hash_path = brick_to_hash_file_path(brick_file, brick_root)
    if hash_path != None:
        if debug:
            print('[debug] remove {0} at {1}'.format(brick_file, hash_path))
        else:
            print('remove {0} at {1}'.format(brick_file, hash_path))
            try:
                os.remove(hash_path)
                try:
                    os.remove(brick_file)
                except:
                    print('Error in removing {0}'.format(brick_file))
            except OSError as e:
                print('Error in removing {0}'.format(hash_path))
                if e.errno == 2:
                    print('Underlaying gluster file does not exist. Just remove the link')
                    os.remove(brick_file)

    else:
        if os.path.exists(brick_file):
            if not debug:
                print('File {0} looks like a common file'.format(brick_file))
                print('Remove {0}'.format(brick_file))
                os.remove(brick_file)
            else:
                print('[debug] File {0} looks like a common file'.format(brick_file))
                print('[debug] Remove {0}'.format(brick_file))
        else:
            if not debug:
                print('File {0} may not be in this brick'.format(brick_file))
                if not os.path.exists(brick_file):
                    if os.path.lexists(brick_file):
                        print('File {0} is a broken link'.format(brick_file))
                        os.remove(brick_file)
            else:
                print('[debug] File {0} may not be in this brick'.format(brick_file))
    pass

def rm_handler(volume_path, peer_name = None, debug = True):
    cu = current_user()
    if cu != 'root':
        print('Please run this script in su mode or sudo')
        print('Current user is {0}'.format(cu))
        exit(-1)

    volume_path = os.path.abspath(volume_path)
    (volume_name, mount_point) = extract_volume_mountpoint(volume_path)
    print(volume_name)
    print(mount_point)
    if volume_name == None or mount_point == None:
        print('This path "{0}" is not a path pointed to a gluster filesystem'.format(volume_path))
        exit(-1)

    if peer_name == None:
        # check when the peer name is not None.
        # if the peer_name is set, it means that this command only run locally
        (volume_status, online_brick_num, all_brick_num) = status(volume_name)
        if volume_status == False or online_brick_num != all_brick_num:
            print('Not all bricks are online. The rm command is dangerous. Stop and check the gluster on each peer!!!')
            exit(-1)
        else:
            print('All brick is online. Go ahead')

    if peer_name == None:
        peers = volume_peers_ls(volume_name)
        current_path = os.path.abspath(os.sys.argv[0])
        print('current path: {0}'.format(current_path))
        rm_cmds = []
        for peer in peers:
            cmds = ['ssh', '-o', 'StrictHostKeyChecking=no', '-t', peer, 'sudo', 'python', current_path
                    , 'rm', volume_path
                    , '--peer_name', peer]
            if debug:
                cmds.append('--debug')
            rm_cmds.append(cmds)
        map_local(rm_cmds, 1, 0)
        # remove the directory completely
        if os.path.exists(volume_path):
            cmds = ['rm', '-rf', volume_path]
            if debug:
                print(cmds)
            else:
                robust_exec(cmds)
    else:
        bricks = brick_ls(volume_name, peer_name)
        print(bricks)
        for brick in bricks:
            brick_path = volume_path.replace(mount_point, brick)
            print('Brick path: {0}'.format(brick_path))
            if os.path.isdir(brick_path):
                remove_brick_dir(brick_path, brick, debug = debug)
            else:
                remove_brick_file(brick_path, brick, debug = debug)

def cp_handler(volume_name, relative_path, dest_path, brick_name = None, debug = True):
    if brick_name == None:
        bricks = brick_ls(volume_name)
        for brick in bricks:
            split_brick = brick.split(':')
            peer = split_brick[0]
            brick_path = split_brick[1]
            cmds = ['scp', '-r', peer+':'+os.path.join(brick_path, relative_path), dest_path]
            if debug:
                print(cmds)
            else:
                robust_exec(cmds)
    else:
        split_brick = brick_name.split(':')
        peer = split_brick[0]
        brick_path = split_brick[1]
        cmds = ['scp', '-r', peer+':'+os.path.join(brick_path, relative_path), dest_path]
        if debug:
            print(cmds)
        else:
            robust_exec(cmds)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='glusterhelper.py', description = 'a helper cli for various gluster task')
    # parser.add_argument('master_name', help = "the host name of the master machine that holds the primary user and group information")
    # parser.add_argument('--debug', dest='debug',action='store_true', help='enable debug mode, so the commands are not executed')
    # parser.set_defaults(debug=False)
    subparser = parser.add_subparsers()

    firewall_parser = subparser.add_parser('firewall', help = 'set firewall rules for gluster')
    firewall_parser.add_argument('--max_brick_num', type = int, default = 200, help = 'the maximal number of bricks')
    firewall_parser.set_defaults(func=lambda args: firewall(args.max_brick_num))

    install_parser = subparser.add_parser('install', help = 'install gluster')
    install_parser.add_argument('--version', default='LATEST', type = str, help='the version of glusterfs to install')
    install_parser.set_defaults(func=lambda args: install(version=args.version))

    mount_parser = subparser.add_parser('mount', help = 'mount a gluster volume and set it as a service')
    mount_parser.add_argument('volume_name', type = str, help = 'the gluster volume')
    mount_parser.add_argument('mount_point', type = str, help = 'mount point')
    mount_parser.add_argument('--host', type = str, default = '127.0.0.1', help = 'the host of gluster volume')
    mount_parser.set_defaults(func=lambda args: mount(args.volume_name, args.mount_point, args.host))

    status_parser = subparser.add_parser('status', help = 'check status of gluster')
    status_parser.add_argument('volume_name', type = str, help = 'the gluster volume')
    status_parser.set_defaults(func=lambda args: status(args.volume_name))

    rm_parser = subparser.add_parser('rm', help = 'remove files or directories in gluster brick directly')
    rm_parser.add_argument('volume_path', type = str, help = 'the gluster volume')
    # rm_parser.add_argument('volume_name', type = str, help = 'the gluster volume')
    # rm_parser.add_argument('mount_point', type = str, help = 'the gluster volume')
    rm_parser.add_argument('--peer_name', default = None, type = str, help = 'the gluster volume')
    rm_parser.add_argument('--debug', dest='debug', action='store_true', help = '')
    rm_parser.set_defaults(debug=False)
    rm_parser.set_defaults(func=lambda args: rm_handler(args.volume_path
                            # , args.volume_name
                            # , args.mount_point
                            , peer_name = args.peer_name
                            , debug = args.debug))

    cp_parser = subparser.add_parser('cp', help = 'copy files or directories in gluster brick directly')
    cp_parser.add_argument('volume_name', type = str, help = 'the gluster volume name')
    cp_parser.add_argument('relative_path', type = str, help = 'the relative path')
    cp_parser.add_argument('dest_path', default = None, type = str, help = 'the destination to copy files to')
    cp_parser.add_argument('--brick_name', default = None, type = str, help = 'the specified brick to copy')
    cp_parser.add_argument('--debug', dest= 'debug', action='store_true', help = '')
    cp_parser.set_defaults(debug=False)
    cp_parser.set_defaults(func=lambda args: cp_handler(args.volume_name
                            , args.relative_path
                            , args.dest_path
                            , brick_name = args.brick_name
                            , debug = args.debug))

    args = parser.parse_args()
    args.func(args)
