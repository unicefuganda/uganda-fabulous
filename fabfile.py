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

def hello():
    print ("Hello Uganda!")



# Schemamigrations specfic
def migrate_app_schema(app,opts='init'):
    #app-> `string` and name of app
    #default option is init
    #opts can take --auto, --add-field, etc.
    run("./manage.py schemamigration %s --%s"%(app,opts))

def run_init_schemamigration_project_apps(app_list):
    """
    migrate app; ./migrate <app_name> --init
    """
    for a in app_list:
        migrate_app_schema(a)

def run_auto_schemamigration_project_apps(app_list):
    """
    migrate app automatically
    """
    for a in app_list:
        migrate_app_schema(a,opts='auto')

# Migrations specific
def migrate_app(app):
    run("./manage.py migrate %s"%app)

def run_auto_migrate_project_apps(app_list):
    """
    migrate apps with southmigration history
    This function detects app's migration state automatically and
     applies the necessary migration.
    """
    for a in app_list:
        migrate_schema(a,)
        run( "./manage.py migrate %s --auto" % a )

def run_migrate_project_apps(app_list):
    """
    Run migrate command on each migration
    """
    for a in app_list:
        migrate_app(a)



def deploy(project='all', dest='test', fix_owner=True,syncdb=False,south=False,south_initial=False):
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
            run("git pull origin master")
            run("git submodule sync")
            run("git submodule update")
            run("git submodule foreach git config core.filemode false")
            with cd("%s_project"%p):
		if syncdb:
		    run("/var/www/env/%s/bin/python manage.py syncdb"%dest)
		if south:
		    run("/var/www/env/%s/bin/python manage.py syncdb"%dest)
		    if south_initial:
		        run("/var/www/env/%s/bin/python manage.py migrate --fake"%dest)
                    run("/var/www/env/%s/bin/python manage.py migrate"%dest)
            
        if not fix_owner == 'False':
            with cd("%s../" % code_dir):
                sudo("chown -R www:www %s" % p)
                sudo("chmod -R ug+rwx %s" % p)

        if dest == 'prod':
            with cd(code_dir):
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
        with settings(warn_only=True):
            local("sudo -u postgres dropdb %s" % p)
        local("sudo -u postgres createdb %s" % p)
        local("scp %s:/tmp/%s.pgsql /tmp/%s.pgsql" % (env.host_string, p, p))
        local("sudo -u postgres psql %s < /tmp/%s.pgsql" % (p, p))
        if not from_local == 'True':
            sudo("rm /tmp/%s.pgsql" % p, user="postgres")

        if not delete_local == 'False':
            local("rm /tmp/%s.pgsql" % p)

#TODO call to backup function for db's prior to a migration; only reinstate backed up DB on failure
def backup_db(project='all'):
    pass



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
