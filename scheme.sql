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

insert into T_ROLE (NAME, DESCRIPTION) values ('USER', '用户');
insert into T_ROLE (NAME, DESCRIPTION) values ('MANAGEMENT', '系统管理');
insert into T_GROUP (NAME, DESCRIPTION) values ('用户', '用户组');
insert into T_GROUP (NAME, PARENT_ID, DESCRIPTION) values ('管理员', 1, '管理员组');
insert into T_GROUP_ROLE (GROUP_ID, ROLE_ID) select 2 as GROUP_ID, ID as ROLE_ID from T_ROLE;
insert into T_USER (USERNAME, PASSWORD, NAME) values ('admin', '', '管理员');
insert into T_USER_GROUP (USER_ID, GROUP_ID) values (1, 2);
