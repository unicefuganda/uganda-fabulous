
    fab deploy:dest={env},project={project} -H {webserver}

  - `env` is one of ['test', 'prod']
  - `project` is one of ['mtrack', 'ureport', 'emis', 'edtrac', 'status160']
  - `webserver` is the host to deploy to.
