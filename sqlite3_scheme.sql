-- 角色表 --
create table T_ROLE (
    ID              integer autoincrement,
    NAME            varchar(256),
    DESCRIPTION     varchar(1024),
    IS_GROUP        integer,
	PARENT_ID       integer,
    primary key (ID)
);
create index IDX_ROLE_NAME on T_ROLE (NAME);

-- 组表 --
create table T_GROUP (
    ID              integer autoincrement,
    NAME            varchar(256),
    PARENT_ID       integer,
    DESCRIPTION     varchar(1024),
    primary key (ID)
);
create index IDX_GROUP_NAME on T_GROUP (NAME);
create index IDX_GROUP_PARENT_ID on T_GROUP (PARENT_ID);

-- 组角色关联表 --
create table T_GROUP_ROLE (
    GROUP_ID    integer,
    ROLE_ID     integer,
    primary key (GROUP_ID, ROLE_ID)
);
create index IDX_GROUP_ROLE_GROUP_ID on T_GROUP_ROLE (GROUP_ID);
create index IDX_GROUP_ROLE_ROLE_ID on T_GROUP_ROLE (ROLE_ID);

-- 用户表 -- 
create table T_USER (
    ID              integer autoincrement,
    USERNAME        varchar(256),
    PASSWORD        varchar(256),
    NAME            varchar(256),
    primary key (ID)
);
create index IDX_USER_USERNAME on T_USER (USERNAME);
create index IDX_USER_NAME on T_USER (NAME);

-- 用户组关联表 --
create table T_USER_GROUP (
    USER_ID     integer,
    GROUP_ID    integer,
    primary key (USER_ID, GROUP_ID)
);
create index IDX_USER_GROUP_USER_ID on T_USER_GROUP (USER_ID);
create index IDX_USER_GROUP_GROUP_ID on T_USER_GROUP (GROUP_ID);

-- 用户角色关联表 --
create table T_USER_ROLE (
    USER_ID     integer,
    ROLE_ID     integer,
    primary key (USER_ID, ROLE_ID)
);
create index IDX_USER_ROLE_USER_ID on T_USER_ROLE (USER_ID);
create index IDX_USER_ROLE_ROLE_ID on T_USER_ROLE (ROLE_ID);

-- 日志表 --
create table T_LOG (
    ID              integer autoincrement,
    TIME            timestamp,
    OPERATOR		integer,
    RESOURCE_NAME   varchar(256),
    RESOURCE_PATH   varchar(1024),
    ARGUMENTS       varchar(4096),
    STATUS          integer,
    MESSAGE         varchar(4096),
	primary key(ID)
);
create index IDX_LOG_TIME on T_LOG (TIME);
create index IDX_LOG_OPERATOR on T_LOG (OPERATOR);

-- 建表sql --
create table T_ROLE (ID integer primary key autoincrement, NAME varchar(256), DESCRIPTION varchar(1024), IS_GROUP integer, PARENT_ID integer);
create index IDX_ROLE_NAME on T_ROLE (NAME);
create table T_GROUP (ID integer primary key autoincrement, NAME varchar(256), PARENT_ID integer, DESCRIPTION varchar(1024));
create index IDX_GROUP_NAME on T_GROUP (NAME);
create index IDX_GROUP_PARENT_ID on T_GROUP (PARENT_ID);
create table T_GROUP_ROLE (GROUP_ID integer, ROLE_ID integer, primary key (GROUP_ID, ROLE_ID));
create index IDX_GROUP_ROLE_GROUP_ID on T_GROUP_ROLE (GROUP_ID);
create index IDX_GROUP_ROLE_ROLE_ID on T_GROUP_ROLE (ROLE_ID);
create table T_USER (ID integer primary key autoincrement, USERNAME varchar(256), PASSWORD varchar(256), NAME varchar(256));
create index IDX_USER_USERNAME on T_USER (USERNAME);
create index IDX_USER_NAME on T_USER (NAME);
create table T_USER_GROUP (USER_ID integer, GROUP_ID integer, primary key(USER_ID, GROUP_ID));
create index IDX_USER_GROUP_USER_ID on T_USER_GROUP (USER_ID);
create index IDX_USER_GROUP_GROUP_ID on T_USER_GROUP (GROUP_ID);
create table T_USER_ROLE (USER_ID integer, ROLE_ID integer, primary key (USER_ID, ROLE_ID));
create index IDX_USER_ROLE_USER_ID on T_USER_ROLE (USER_ID);
create index IDX_USER_ROLE_ROLE_ID on T_USER_ROLE (ROLE_ID);
create table T_LOG (ID integer primary key autoincrement, TIME timestamp, OPERATOR integer, RESOURCE_NAME varchar(256), RESOURCE_PATH varchar(1024), ARGUMENTS varchar(4096), STATUS integer, MESSAGE varchar(4096));
create index IDX_LOG_TIME on T_LOG (TIME);
create index IDX_LOG_OPERATOR on T_LOG (OPERATOR);

-- 初始化角色 --
insert into T_ROLE (NAME, DESCRIPTION, IS_GROUP, PARENT_ID) values ('USER', '用户', 0, 0);
insert into T_ROLE (NAME, DESCRIPTION, IS_GROUP, PARENT_ID) values ('SYS_ADMIN', '系统管理', 1, 0);
insert into T_ROLE (NAME, DESCRIPTION, IS_GROUP, PARENT_ID) values ('SYS_USER', '用户/组/角色管理', 0, (select ID from T_ROLE where NAME = 'SYS_ADMIN'));
insert into T_ROLE (NAME, DESCRIPTION, IS_GROUP, PARENT_ID) values ('SYS_LOG', '系统日志', 0, (select ID from T_ROLE where NAME = 'SYS_ADMIN'));
insert into T_ROLE (NAME, DESCRIPTION, IS_GROUP, PARENT_ID) values ('MANAGEMENT', '内容管理', 1, 0);
insert into T_ROLE (NAME, DESCRIPTION, IS_GROUP, PARENT_ID) values ('BLOG_MGR', '日志管理', 0, (select ID from T_ROLE where NAME = 'MANAGEMENT'));
insert into T_ROLE (NAME, DESCRIPTION, IS_GROUP, PARENT_ID) values ('ALBUM_MGR', '相片管理', 0, (select ID from T_ROLE where NAME = 'MANAGEMENT'));

-- 角色初始化完毕 --
insert into T_GROUP (NAME, DESCRIPTION) values ('用户', '用户组');
insert into T_GROUP (NAME, PARENT_ID, DESCRIPTION) values ('管理员', (select ID from T_GROUP where NAME = '用户'), '管理员组');
insert into T_USER (USERNAME, PASSWORD, NAME) values ('admin', '', '管理员');
insert into T_USER_GROUP (USER_ID, GROUP_ID) values ((select ID from T_USER where USERNAME = 'admin'), (select ID from T_GROUP where NAME = '管理员'));

-- 每次新增角色后执行下面2条语句 --
delete from T_GROUP_ROLE where GROUP_ID = (select ID from T_GROUP where NAME = '管理员');
insert into T_GROUP_ROLE (GROUP_ID, ROLE_ID) select (select ID from T_GROUP where NAME = '管理员') as GROUP_ID, ID as ROLE_ID from T_ROLE where IS_GROUP = 0;
