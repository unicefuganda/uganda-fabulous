
    fab deploy:dest={env},project={project},settings_module={module_name} -H {webserver}

  - `env` is one of ['test', 'prod']
  - `project` is one of ['mtrack', 'ureport', 'emis', 'edtrac', 'status160']
  - `webserver` is the host to deploy to.
  - `module_name` is optional, but may be used to specify the DJANGO_SETTINGS_MODULE
