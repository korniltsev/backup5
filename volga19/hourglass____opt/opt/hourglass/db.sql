
create table user
(
	id int auto_increment
		primary key,
	username varchar(255) not null,
	password varchar(255) not null,
	registration_date datetime default CURRENT_TIMESTAMP not null,
	constraint user_username_uindex
		unique (username)
);

create table project
(
	id int auto_increment
		primary key,
	user_id int not null,
	name varchar(255) not null,
	constraint project_user_id_fk
		foreign key (user_id) references user (id)
			on delete cascade
);

create table worklog
(
	id int auto_increment
		primary key,
	user_id int not null,
	title varchar(255) not null,
	project_id int null,
	time int not null,
	creation_date datetime default CURRENT_TIMESTAMP null,
	constraint worklog_project_id_fk
		foreign key (project_id) references project (id)
			on delete set null,
	constraint worklog_user_id_fk
		foreign key (user_id) references user (id)
			on delete cascade
);

