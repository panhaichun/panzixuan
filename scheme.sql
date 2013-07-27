create table T_USER (
    ID integer autoincrement, 
    USERNAME varchar(256), 
    PASSWORD varchar(256), 
    NAME varchar(256),
    primary key (ID)
);

create table T_GROUP (
    ID integer autoincrement, 
    NAME varchar(256), 
    PARENT_ID integer, 
    DESCRIPTION varchar(1024),
    primary key (ID)
)

create table T_ROLE (
    ID integer autoincrement, 
    NAME varchar(256), 
    DESCRIPTION varchar(1024),
    primary key (ID)
);

create table T_USER_GROUP (
    USER_ID integer, 
    GROUP_ID integer, 
    primary key (USER_ID, GROUP_ID)
)

create table T_USER_ROLE (
    USER_ID integer, 
    ROLE_ID integer, 
    primary key (USER_ID, ROLE_ID)
);

create table T_GROUP_ROLE (
    GROUP_ID integer, 
    ROLE_ID integer, 
    primary key (GROUP_ID, ROLE_ID)
);
create table T_USER (ID integer primary key autoincrement, USERNAME varchar(256), PASSWORD varchar(256), NAME varchar(256));
create table T_GROUP (ID integer primary key autoincrement, NAME varchar(256), PARENT_ID integer, DESCRIPTION varchar(1024));
create table T_ROLE (ID integer primary key autoincrement, NAME varchar(256), DESCRIPTION varchar(1024));
create table T_USER_GROUP (USER_ID integer, GROUP_ID integer, primary key(USER_ID, GROUP_ID));
create table T_USER_ROLE (USER_ID integer, ROLE_ID integer, primary key (USER_ID, ROLE_ID));
create table T_GROUP_ROLE (GROUP_ID integer, ROLE_ID integer, primary key (GROUP_ID, ROLE_ID));

INSERT INTO T_ROLE (NAME, DESCRIPTION) VALUES ('USER', '用户');
INSERT INTO T_ROLE (NAME, DESCRIPTION) VALUES ('MANAGEMENT', '系统管理');
INSERT INTO T_GROUP (NAME, DESCRIPTION) VALUES ('用户', '用户组');
INSERT INTO T_GROUP (NAME, PARENT_ID, DESCRIPTION) VALUES ('管理员', 1, '管理员组');
INSERT INTO T_GROUP_ROLE (GROUP_ID, ROLE_ID) SELECT 2 AS GROUP_ID, ID AS ROLE_ID FROM T_ROLE;
INSERT INTO T_USER (USERNAME, PASSWORD, NAME) VALUES ('admin', '', '管理员');
INSERT INTO T_USER_GROUP (USER_ID, GROUP_ID) VALUES (1, 2);
