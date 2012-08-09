from fabric.api import env, local, prefix, put, sudo, task, \
     require, puts, cd, run, abort, lcd
from fabric.colors import green, red, cyan, yellow
from fabric.contrib import files
from fabric.context_managers import cd, hide, settings
import georgia_lynchings
import os
import re

'''
Recommended usage:
$ fab -H servername deploy
'''

# default settings
env.remote_path = '/var/www/galyn'
env.remote_acct = 'galyn'
env.url_prefix = ''
env.version = georgia_lynchings.__version__
env.rev_tag = ''

# omit these from the test coverage report
env.omit_test_coverage = ','.join([
    'georgia_lynchings/manage.py',
    'georgia_lynchings/settings.py',
    'georgia_lynchings/localsettings.py',
    ])


@task
def git_source(rev='HEAD'):
    '''Create a tarball of the git source tree.

    Arguments:
      rev: (optional) a git commit identifer, defaults to HEAD
    '''

    # if not a released version, use revision tag
    short_rev = local('git rev-parse --short %s' % (rev,), capture=True)
    env.git_rev = short_rev.strip()
    if georgia_lynchings.__version_info__[-1]:
        env.rev_tag = '-r' + env.git_rev
    env.build_dir = 'galyn-%(version)s%(rev_tag)s' % env
    env.tarball = 'galyn-%(version)s%(rev_tag)s.tar.bz2' % env

    local('mkdir -p build')
    local('rm -rf build/%(build_dir)s' % env)
    # create a tar archive of the specified version and extract inside the bulid directory
    local('git archive --format=tar --prefix=%(build_dir)s/ %(git_rev)s | bzip2 > dist/%(tarball)s' % env)


@task
def push_source():
    '''Deploy the code to a remote server. Assumes a source tarball has already been
    created or specified.

    Usage: fab test doc git_source push_source rm_old_builds
    '''
    require('tarball', provided_by=[git_source],
            used_for='the source tarball to copy and extract')
    require('build_dir', 'tarball', provided_by=[git_source],
            used_for='the source directory that the tarball expands to')

    # check the remote system for required files
    if not files.exists('%(remote_path)s/localsettings.py' % env):
        abort('Configuration file is not in expected location: %(remote_path)s/localsettings.py' % env)

    # copy the source tarball
    put('dist/%(tarball)s' % env,
        '/tmp/%(tarball)s' % env)
    # extract it
    with cd(env.remote_path):
        try:
            sudo('tar xjf /tmp/%(tarball)s' % env, user=env.remote_acct)
        finally:
            run('rm /tmp/%(tarball)s' % env)
        # copy localsettings
        sudo('cp localsettings.py %(build_dir)s/georgia_lynchings/localsettings.py' % env,
             user=env.remote_acct)
    # configure the remote virtualenv
    with cd('%(remote_path)s/%(build_dir)s' % env):
        sudo("virtualenv --no-site-packages env --prompt='(galyn)'" % env,
             user=env.remote_acct)
        with prefix('source env/bin/activate' % env):
            sudo('pip install -r pip-install-req.txt', user=env.remote_acct)
            sudo('python georgia_lynchings/manage.py collectstatic --noinput',
                 user=env.remote_acct)
    # update current/previous links
    with cd(env.remote_path):
        if files.exists('current' % env):
            sudo('rm -f previous; mv current previous', user=env.remote_acct)
        sudo('ln -sf %(build_dir)s current' % env, user=env.remote_acct)

        # sanity-check current localsettings against previous
        if files.exists('previous'):
            with settings(hide('warnings', 'running', 'stdout', 'stderr'),
                          warn_only=True):  # suppress output, don't abort on diff error exit code
                output = sudo('diff current/georgia_lynchings/localsettings.py previous/georgia_lynchings/localsettings.py' % env,
                              user=env.remote_acct)
                if output:
                    puts(yellow('WARNING: found differences between current and previous localsettings.py'))
                    puts(output)
                else:
                    puts(green('No differences between current and previous localsettings.py'))


@task
def push_live():
    '''Update the live website to use the new current deployment.'''
    if not files.exists('%(remote_path)s/current' % env):
        abort("Current software is not linked. Can't make it live.")

    with cd(env.remote_path):
        sudo('rm -f live', user=env.remote_acct)
        sudo('ln -sf $(readlink current) live', user=env.remote_acct)
    sudo('apache2ctl -t')
    sudo('service apache2 restart')


@task
def deploy():
    '''Fully build and test the project, then push the software to the
    configured server and update the live site to use it.
    '''
    test()
    doc()
    git_source()
    push_source()
    push_live()
    rm_old_builds()


@task
def test():
    '''Locally run all tests.'''
    if os.path.exists('test-results'):
        shutil.rmtree('test-results')

    local('coverage run --branch georgia_lynchings/manage.py test --noinput')
    local('coverage xml --include=georgia_lynchings**/*.py --omit=%(omit_coverage)s' % env)


@task
def doc():
    '''Locally build documentation.'''
    with lcd('doc'):
        local('make clean html')


@task
def revert(path=None, user=None):
    '''Update remote symlinks to retore the previous version as current

        Example: fab revert
    '''
    if not files.exists('%(remote_path)s/previous' % env):
        abort("No previous version available to revert to")

    sudo('rm current', user=env.remote_acct)
    sudo('mv previous current', user=env.remote_acct)


@task
def clean():
    '''Remove local build/dist artifacts generated by deploy task
        Example: fab clean
    '''
    local('rm -rf build dist')


@task
def rm_old_builds(noinput=False):
    '''Remove old build directories on the deploy server.

    By default, will ask user to confirm deletion. Use the noinput parameter
    to delete without requesting confirmation.
    '''
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
