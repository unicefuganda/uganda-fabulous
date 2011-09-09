from fabric.api import local, abort, run, cd, settings, sudo

PROJECTS = ['cvs', 'ureport', 'emis', 'status160']

def hello():
    print ("Hello Uganda!")

def deploy(project='all', dest='test'):
    if not dest in ['prod', 'test']:
        abort('must specify a valid dest: prod or test')
    if not (project == 'all' or project in PROJECTS):
        abort('must specify a valid project: all or one of %s' % PROJECTS)
    projects = PROJECTS if project == 'all' else [project]
    for p in projects:
        code_dir = "/var/www/%s/%s/" % (dest, p)
        with settings(warn_only=True):
            if run("test -d %s" % code_dir).failed:
                run("git clone git://github.com/unicefuganda/%s %s" % (p, code_dir))
                with cd(code_dir):
                    run("git submodule init")
        with cd(code_dir):
            run("git pull origin master")
            run("git submodule sync")
            run("git submodule update")
        with cd("%s../" % code_dir):
            sudo("chown -R www:www %s" % p)
            sudo("chmod -R ug+rwx %s" % p)


