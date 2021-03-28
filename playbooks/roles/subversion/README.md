# Configure subversion server

Much of parameters should be configured in `vars/main.yml`

Common parameters:

- repo_list
- rsync_args

## Support tools

Should go to the files/tools
TODO: convert it to ansible-agnostic library


## Configure ./conf

### ./conf/authz

Default:

- tool_authz_dryrun: false
- tool_authz_bindpass: must be configured

### ./conf/hools-env

Defaults:

- hooks_env_codepage: C.UTF-8

## Hooks

Put 'em to files/hooks. Shared code goes to `_shared_scripts_`

Final deploy will look like this:

```j2
_shared_scripts_/*  => {{ repos_home }}/_shared_scripts_/
{{ репозиторий }}/* => {{ repos_home }}/{{ репозиторий }}/hooks/
```

### Debuggin hooks (windows)

1. Configure local repo

```cmd
Set SVNROOT=c:\svnroot
Set REPO=xom
Set GIT_PROJ_PATH=C:\gitlab\ansible

Rem Create test repos root directory
Mkdir %SVNROOT%
Cd /D %SVNROOT%

mklink /D %GIT_PROJ_PATH%\playbooks\roles\subversion\files\_shared_scripts_ _shared_scripts_

svnadmin create %REPO%
mklink %GIT_PROJ_PATH%\playbooks\roles\subversion\files\hooks\xom\pre-commit ^
    %REPO%\hooks\pre-commit
```

1. Checkout nearby the working directory
1. If already done step 1., disable pre-commit hook and do some commits
1. Enable the hookand run tests by commited revision

```cmd
Set REVISION=8
python3 %GIT_PROJ_PATH%\playbooks\roles\subversion\files\hooks\svnproject\pre-commit %SVNROOT%\%REPO% %REVISION%
```