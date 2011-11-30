from fabric.api import local, abort, run, lcd, cd, settings, sudo, env
from fabric.contrib.console import confirm

PROJECTS = ['mtrack', 'ureport', 'emis', 'status160']
STANDARD_REPOS = [
   'django-eav',
   'rapidsms',
   'rapidsms-auth',
   'rapidsms-contact',
   'rapidsms-generic',
   'rapidsms-healthmodels',
   'rapidsms-httprouter',
   'rapidsms-polls',
   'rapidsms-script',
   'rapidsms-uganda-common',
   'rapidsms-unregister',
   'rapidsms-ureport',
   'rapidsms-xforms',
]

REPOS_WITH_SRC_NAME = [
    'rapidsms-httprouter',
    'rapidsms-xforms'
]

def deploy(project='all', dest='test', fix_owner='True', syncdb='False', south='False', south_initial='False', init_data='False',hash='False'):
    print "Fix owner is %s" % fix_owner
    if not dest in ['prod', 'test']:
        abort('must specify a valid dest: prod or test')
    if project != 'all' and project not in PROJECTS \
        and not confirm("Project %s not in known projects (%s), proceed anyway?" % (project, PROJECTS)):
        abort('must specify a valid project: all or one of %s' % PROJECTS)
    projects = PROJECTS if project == 'all' else [project]
    for p in projects:
        #/var/www/test/upreport
        code_dir = "/var/www/%s/%s/" % (dest, p)
        with settings(warn_only=True):
            if run("test -d %s" % code_dir).failed:
                run("git clone git://github.com/unicefuganda/%s %s" % (p, code_dir))
                with cd(code_dir):
                    run("git submodule init")
                    run("git config core.filemode false")
        with cd(code_dir):
            if hash == 'False':
            	run("git pull origin master")
	    else:
                run("git checkout %s"%hash)
            run("git submodule sync")
            run("git submodule update")
            run("git submodule foreach git config core.filemode false")
            with cd("%s_project" % p):
                if syncdb == 'True':
                    run("/var/www/env/%s/bin/python manage.py syncdb" % dest)
                if south == 'True':
                    run("/var/www/env/%s/bin/python manage.py migrate" % dest)
                if init_data == 'True':
                   # in mtrack, this loads initial data
                   # which doesn't specifically mean fixtures (which are loaded during syncdb and  migrations)
                   run("/var/www/env/%s/bin/python manage.py %s_init" % (dest, p))
                if south_initial == 'True':
                    run("/var/www/env/%s/bin/python manage.py migrate --fake" % dest)
                    run("/var/www/env/%s/bin/python manage.py migrate" % dest)

        if not fix_owner == 'False':
            with cd("%s../" % code_dir):
                sudo("chown -R www:www %s" % p)
                sudo("chmod -R ug+rwx %s" % p)

        if dest == 'prod':
            with cd(code_dir):
                with settings(warn_only=True):
                    sudo("cp cron_* /etc/cron.d/")
                sudo("service cron restart")

        proc_name = "test%s" % p if dest == 'test' else p
        sudo("supervisorctl restart %s" % proc_name)


def copy_db(project='all'):
    if project != 'all' and project not in PROJECTS \
        and not confirm("Project %s not in known projects (%s), proceed anyway?" % (project, PROJECTS)):
        abort('must specify a valid project: all or one of %s' % PROJECTS)
    projects = PROJECTS if project == 'all' else [project]

    for p in projects:
        sudo("pg_dump %s > /tmp/%s.pgsql" % (p, p), user="postgres")
        with settings(warn_only=True):
            sudo("dropdb %s-test" % p, user="postgres")
        sudo("createdb %s-test" % p, user="postgres")
        sudo("psql %s-test < /tmp/%s.pgsql" % (p, p), user="postgres")
        sudo("rm /tmp/%s.pgsql" % p, user="postgres")


def pull_db(project='all', delete_local=True, from_local=False):
    if project != 'all' and project not in PROJECTS \
        and not confirm("Project %s not in known projects (%s), proceed anyway?" % (project, PROJECTS)):
        abort('must specify a valid project: all or one of %s' % PROJECTS)
    projects = PROJECTS if project == 'all' else [project]
    for p in projects:
        if not from_local == 'True':
            sudo("pg_dump %s > /tmp/%s.pgsql" % (p, p), user="postgres")
            local("scp %s:/tmp/%s.pgsql /tmp/%s.pgsql" % (env.host_string, p, p))
            sudo("rm /tmp/%s.pgsql" % p, user="postgres")
        with settings(warn_only=True):
            local("sudo -u postgres dropdb %s" % p)
        local("sudo -u postgres createdb %s" % p)
        local("sudo -u postgres psql %s < /tmp/%s.pgsql" % (p, p))
        if not delete_local == 'False':
            local("rm /tmp/%s.pgsql" % p)


def add_all_submodules(project, dev=False):
        with settings(warn_only=True):
            if local("test -d %s_project" % project).failed:
                local("mkdir %s_project" % project)
        for repo in STANDARD_REPOS:
            if not repo in REPOS_WITH_SRC_NAME:
                dest_folder = "%s_project/%s" % (project, repo.replace("-", "_"))
            else:
                dest_folder = "%s_project/%s_src" % (project, repo.replace("-", "_"))
            with settings(warn_only=True):
                if local("test -d %s" % dest_folder).failed:
                    local("git submodule add git://github.com/unicefuganda/%s %s" % (repo, dest_folder))
                if dev == 'True':
                    with settings(warn_only=False):
                        with lcd(dest_folder):
                            local("git remote add dev git@github.com:unicefuganda/%s" % repo)
