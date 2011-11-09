from fabric.api import env, local, prefix, put, sudo, task, \
     require, puts, cd, run, abort
from fabric.colors import green, red, cyan
from fabric.contrib import files
from fabric.context_managers import cd, hide, settings
import georgia_lynchings
import os
import re

'''
Overview
========

A basic build deploy script for georgia_lynchings, using Fabric 1.1 or greater.

Usage
-----

To initialize a Sesame RDF triplestore with data from a PC-ACE MDB (MS
Access) file, run the **load_triples** task with the path to the MDB file
and the location of the Sesame repository. To deploy the code, run the
**deploy** task with parameters and a remote server. To undo a deploy, run
the **revert** task with the same parameters. To clean up local deploy
artifacts, use the **clean** task. For more details, use ``fab -d`` with
the task name that you are interested in.

'''

# default settings
env.rev_tag = ''
env.remote_venv_path = '/home/httpd/sites/virtual_envs/georgia_lynchings'
env.remote_path = '/home/httpd/georgia_lynchings'
env.remote_acct = 'galyn'
env.url_prefix = ''

# omit these from the test coverage report
env.omit_coverage = ','.join([
    'georgia_lynchings/manage.py',
    'georgia_lynchings/settings.py',
    'georgia_lynchings/localsettings.py',
    ])

@task
def load_triples(mdb_path, sesame_repo, keep_files=False):
    '''Load RDF triples from a PC-ACE MDB (MS Access) file into a Sesame RDF
    triplestore.

    The task will create a temporary directory for intermediary CSV and
    TTL files, which it will then upload to the triplestore and add any
    other necessary configuration and RDF statements.

    Usage: fab load_triples:<mdb_path>,<sesame_repo>[,keep_files=True]

    Parameters:
      mdb_path: path to source MDB file; e.g., path/to/pc-ace.mdb
      sesame_repo: URL of the target repository. The repository must already
            exist and should be empty. e.g.:
                http://server:port/openrdf-sesame/respositories/my-repo
      keep_files: optional. Specify as "True" to keep the directory of
            temporary files intact. Without this option, the temporary
            directory will be deleted after upload is complete.
    '''

    data_dir = local('mktemp -d', capture=True)
    try:
        local('scripts/mdb2csv.sh "%s" "%s"' % (mdb_path, data_dir))
        local('scripts/csv2rdf.py "%s"/*.csv' % (data_dir,))
        local('scripts/add-rdf-namespaces.sh -r "%s"' % (sesame_repo,))
        local('scripts/upload-ttl.sh -r "%s"/statements "%s"/*.ttl' %
              (sesame_repo, data_dir))
        local('scripts/add-inferred-statements.sh "%s"/statements' %
              (sesame_repo,))
    finally:
        if not keep_files:
            local('rm -rf ' + data_dir)
    
def configure(path=None, user=None, url_prefix=None, remote_venv_path=None):
    'Configuration settings used internally for the build.'
    env.version = georgia_lynchings.__version__
    config_from_git()
    # construct a unique build directory name based on software version and svn revision
    env.build_dir = 'georgia_lynchings-%(version)s%(rev_tag)s' % env
    env.tarball = 'georgia_lynchings-%(version)s%(rev_tag)s.tar.bz2' % env

    if path:
        env.remote_path = path.rstrip('/')
    if user:
        env.remote_acct = user
    if url_prefix:    
        env.url_prefix = url_prefix.rstrip('/')
    if remote_venv_path:
        env.remote_venv_path = remote_venv_path
        puts('setting virtual environment to %(remote_venv_path)s' % env)


def config_from_git():
    """Infer revision from local git checkout."""
    # if not a released version, use revision tag 
    env.git_rev = local('git rev-parse --short HEAD', capture=True).strip()
    if georgia_lynchings.__version_info__[-1]:
        env.rev_tag = '-r' + env.git_rev

def prep_source():
    'Export the code from git and do local prep.'
    require('git_rev', 'build_dir',
            used_for='Exporting code from git into build area')
    
    local('mkdir -p build')
    local('rm -rf build/%(build_dir)s' % env)
    # create a tar archive of the specified version and extract inside the bulid directory
    local('git archive --format=tar --prefix=%(build_dir)s/ %(git_rev)s | (cd build && tar xf -)' % env)
    
    # localsettings.py will be handled remotely

    # update wsgi file if a url prefix is requested
    if env.url_prefix:
        env.apache_conf = 'build/%(build_dir)s/apache/georgia_lynchings.conf' % env
        puts(cyan('Updating apache config %(apache_conf)s with url prefix %(url_prefix)s' % env))
        # back up the unmodified apache conf
        orig_conf = env.apache_conf + '.orig'
        local('cp %s %s' % (env.apache_conf, orig_conf))
        with open(orig_conf) as original:
            text = original.read()
        text = text.replace('WSGIScriptAlias / ', 'WSGIScriptAlias %(url_prefix)s ' % env)
        text = text.replace('Alias /static/ ', 'Alias %(url_prefix)s/static ' % env)
        text = text.replace('<Location />', '<Location %(url_prefix)s/>' % env)

        with open(env.apache_conf, 'w') as conf:
            conf.write(text)
           
    # update wsgi file if a virtual env path is defined in the conf file
    if env.remote_venv_path:
        env.apache_conf = 'build/%(build_dir)s/apache/georgia_lynchings.conf' % env
        puts(cyan('Updating apache config %(apache_conf)s with url prefix %(url_prefix)s' % env))
        # back up the unmodified apache conf
        orig_conf = env.apache_conf + '.orig2'
        local('cp %s %s' % (env.apache_conf, orig_conf))
        with open(orig_conf) as original:
            text = original.read()
        # replace the virtual path in the wsgi conf file.
        text = text.replace('[VIRTUAL_ENV]', '%(remote_venv_path)s' % env)
        
        with open(env.apache_conf, 'w') as conf:
            conf.write(text)
            
    # update wsgi file if a virtual env path is defined in the wsgi file
    if env.remote_venv_path:
        env.apache_conf = 'build/%(build_dir)s/apache/georgia_lynchings.wsgi' % env
        puts(cyan('Updating apache config %(apache_conf)s with url remote_venv_path %(remote_venv_path)s' % env))
        # back up the unmodified apache conf
        orig_conf = env.apache_conf + '.worig'
        local('cp %s %s' % (env.apache_conf, orig_conf))
        with open(orig_conf) as original:
            text = original.read()
        # replace the virtual path in the wsgi conf file.
        patn=r'''[\s]*(os.environ['VIRTUAL_ENV'])([\s]+=[\s]+)([^$]+)$'''
        replacemt=r'''\1\2\'%(remote_venv_path)s\'''' % env         
        text = re.sub(patn, replacemt, text)   
        
        with open(env.apache_conf, 'w') as conf:
            conf.write(text)            

def package_source():
    'Create a tarball of the source tree.'
    local('mkdir -p dist')
    local('tar cjf dist/%(tarball)s -C build %(build_dir)s' % env)

# remote functions

def upload_source():
    'Copy the source tarball to the target server.'
    puts(cyan('Copy the source tarball to the target server.'))    
    put('dist/%(tarball)s' % env,
        '/tmp/%(tarball)s' % env)

def extract_source():
    'Extract the remote source tarball under the configured remote directory.'
    with cd(env.remote_path):
        sudo('tar xjf /tmp/%(tarball)s' % env, user=env.remote_acct)
        # if the untar succeeded, remove the tarball
        run('rm /tmp/%(tarball)s' % env)
        # update apache.conf if necessary

def setup_virtualenv():
    'Create a virtualenv and install required packages on the remote server.'
    with cd('%(remote_path)s/%(build_dir)s' % env):    
        # create the virtualenv under the build dir
        sudo('virtualenv --no-site-packages %(remote_venv_path)s' % env,
             user=env.remote_acct)
        # activate the environment and install required packages
        with prefix('source %(remote_venv_path)s/bin/activate' % env):
            pip_cmd = 'pip install -r pip-install-req.txt'
            sudo(pip_cmd, user=env.remote_acct)

def configure_site():
    'Copy configuration files into the remote source tree.'
    with cd(env.remote_path):
        if not files.exists('localsettings.py'):  
            abort('Configuration file is not in expected location: %(remote_path)s/localsettings.py' % env)
        sudo('cp localsettings.py %(build_dir)s/georgia_lynchings/localsettings.py' % env,
             user=env.remote_acct)

def update_links():
    'Update current/previous symlinks on the remote server.'
    with cd(env.remote_path):
        if files.exists('current' % env):
            sudo('rm -f previous; mv current previous', user=env.remote_acct)
        sudo('ln -sf %(build_dir)s current' % env, user=env.remote_acct)


def build_source_package(path=None, user=None, url_prefix='', remote_venv_path=''):
    '''Produce a tarball of the source.  '''
    configure(path, user, url_prefix, remote_venv_path)
    prep_source()
    package_source()
    
@task    
def test():
    '''Locally run all tests.'''
    if os.path.exists('test-results'):
        shutil.rmtree('test-results')

    local('coverage run --branch georgia_lynchings/manage.py test --noinput')
    local('coverage xml --include=georgia_lynchings**/*.py --omit=%(omit_coverage)s' % env)

def doc():
    '''Locally build documentation.'''
    with lcd('doc'):
        local('make clean html')       

@task
def deploy(path=None, user=None, url_prefix='', remote_venv_path=''):
    '''Deploy the code to a remote server.
    
    Usage: fab deploy <path> <user> <url_prefix> <remote_venv_path>
    
    Parameters:
      path: base deploy directory on remote host; deploy expects a
            localsettings.py file in their directory
            Default: /home/httpd/sites/georgia_lynchings
      user: user on the remote host to run the deploy; ssh user (current or
            specified with -U option) must have sudo permission to run deploy
            tasks as the specified user
            Default: galyn
      url_prefix: base url if site is not deployed at /
      remote_venv_path: virtual environment path on the remote server

    Example usage: fab deploy:path=/home/httpd/sites/georgia_lynchings,url_prefix=/georgia_lynchings,remote_venv_path=/home/httpd/sites/virtual_envs/georgia_lynchings -H username@servername
    '''
    # local to jenkins
    build_source_package(path, user, url_prefix, remote_venv_path)
    test()
    doc()
    # local to /home/httpd/georgia_lynchings
    upload_source()
    extract_source()
    setup_virtualenv()
    configure_site()
    update_links()


    puts(green('Successfully deployed %(build_dir)s to %(host)s' % env))

@task
def revert(path=None, user=None):
    '''Update remote symlinks to retore the previous version as current

        Example: fab revert    
    '''
    configure(path, user)
    # if there is a previous link, shift current to previous
    if files.exists('previous'):
        # remove the current link (but not actually removing code)
        sudo('rm current', user=env.remote_acct)
        # make previous link current
        sudo('mv previous current', user=env.remote_acct)
        sudo('readlink current', user=env.remote_acct)

@task
def clean():
    '''Remove local build/dist artifacts generated by deploy task
        Example: fab clean    
    '''
    local('rm -rf build dist')

@task
def rm_old_builds(path=None, user=None, noinput=False):
    '''Remove old build directories on the deploy server.

    By default, will ask user to confirm deletion.  
    Use the noinput parameter to delete without requesting confirmation.
    
    Usage: fab rm_old_builds [path] [user] [noinput]
    
    Parameters:
      path: base deploy directory on remote host; deploy expects a
            localsettings.py file in their directory
            Default: /home/httpd/sites/georgia_lynchings
      user: user on the remote host to run the deploy; ssh user (current or
            specified with -U option) must have sudo permission to run deploy
            tasks as the specified user
            Default: galyn
      noinput: delete without requesting confirmation
            Default: False

    Example usage: fab rm_old_builds:path=/home/httpd/sites/georgia_lynchings -H username@servername
    '''
    configure(path, user)
    with cd(env.remote_path):
        with hide('stdout'):  # suppress ls/readlink output
            # get directory listing sorted by modification time (single-column for splitting)
            dir_listing = sudo('ls -t1', user=env.remote_acct)
            # get current and previous links so we don't remove either of them
            current = sudo('readlink current', user=env.remote_acct) if files.exists('current') else None
            previous = sudo('readlink previous', user=env.remote_acct) if files.exists('previous') else None
            
        # split dir listing on newlines and strip whitespace
        dir_items = [n.strip() for n in dir_listing.split('\n')] 
        # regex based on how we generate the build directory:
        #   project name, numeric version, optional pre/dev suffix, optional revision #
        build_dir_regex = r'^georgia_lynchings-[0-9.]+(-[A-Za-z0-9_-]+)?(-r[0-9a-f]+)?$' % env
        build_dirs = [item for item in dir_items if re.match(build_dir_regex, item)]
        # by default, preserve the 3 most recent build dirs from deletion
        rm_dirs = build_dirs[3:]
        # if current or previous for some reason is not in the 3 most recent,
        # make sure we don't delete it
        for link in [current, previous]:
            if link in rm_dirs:
                rm_dirs.remove(link)

        if rm_dirs:
            for dir in rm_dirs:
                if noinput or confirm('Remove %s/%s ?' % (env.remote_path, dir)):
                    sudo('rm -rf %s' % dir, user=env.remote_acct)
        else:
            puts('No old build directories to remove')
 
