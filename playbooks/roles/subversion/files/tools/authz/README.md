# ldap2svnAuthz
## Назначение
Генерирует на основе файла конфигурации (yaml) файл доступов conf/authz

## Использование
Файл конфигурации выполнен в синтаксисе [YAML 1.1](http://yaml.org/spec/1.1/) и содержит два основных "блока":

1. `ldap' - здесь указывается информация касательно подключения к лдап-серверу, различные предефайны для работы с лдап.
1. `access' - здесь конфигурятся доступы.

### Конфигурация доступов ("блок" access: )

```
 Доступы могут конфигуриться так (здесь '|' означает "или так"):
  <имя репозитория> | default :
      Имя АД-объекта(группа или пользователь):
          type: user|group
          perms: доступ: r|w|'' # perms можно не указывать. По дефолту будет 'r'


  <Предопределенное имя> : <права доступа>
 , где <Предопределенное имя> может быть: 
        DEFAULT_GROUP == префикс 'svn_' + имя репозитория
          Например, для репы emo предопределенное имя АД-группы будет svn_emo        

        EVERYONE == суть '*' в authz. Если не указано, по дефолту EVERYONE = ''
 ....

 ПРИМЕР
access:
  somerepo:
        администраторы всего и вся:
            type: group
            perms: rw
        EVERYONE: ''

 Внимание: АД-группы траверсятся на один уровень.. Пробелы в имени группы и русские буквы нормально обрабатываются в authz
 Т.е. вот такое содержимое authz (utf-8) вполне норм. понимается:
  [groups]
  Доменные админы = petya_vasin, vasya_petin
  [/]
  @Доменные админы = rw

```
### Фильтр юзеров
По дефолту из группы добываются только те учетки, которые не задизаблены

### Юникод и прочие безобразия
Все что названо по-русски (группы, учетки) должно нормально пониматься, в том числе
внутри самого файла authz сервером svn. Тесты показали, что даже вот такое authz нормально понимает:
```

[groups]
Мега крутая группа менеджеров = Вася Первый, Петя Второй, А. Лександр Уволенный

[/]
@Мега крутая группа менеджеров = ''
```

### Траверс АД-групп
Члены вложенных групп будут так же включены в authz файл с правами родителя.
Поддерживается только первый уровень вложенности


### Приоритеты задания параметров конфигурации

 сверху наивысший:
1. Параметры командной строки
1. Переменные среды
1. Параметры в конфигурационном файле
1. Параметры внутри кода скрипта

Например.
 Параметр 'url', сконфигурирован :
 1. внутри кода скрипта: url = "localhost"
 1. в переменной среды LDAP_URL = "ld01.someserver.tld:389"
 1. в конфиге: ldap.url: '192.168.0.100'

 Будет использовано значение ld01.someserver.tld:389


### Правила именования переменных

Некоторые параметры можно задавать переменными окружения по следующим правилам:
LD2SVN_<узел>_<параметр>, например, ```LD2SVN_LDAP_BIND_PW```

Понимаются следующие переменные окружения:
```
LD2SVN_LDAP_URL
LD2SVN_LDAP_BIND_DN
LD2SVN_LDAP_BIND_PW

LD2SVN_SVN_REPOS_ROOT
LD2SVN_SVN_REPO_NAME
LD2SVN_SVN_AUTHZ_PATH
```