drop table if exists user;
create table user
(
	user_id 	integer primary key autoincrement,
	username 	string not null unique,
	email 		string not null,
	pw_hash 	string not null
);

drop table if exists prefs;
create table prefs
(
	user_id		integer not null,
	new_window	boolean default 1
);


drop table if exists feed;
create table feed
(
	feed_id 	integer primary key autoincrement,
	url 		string not null,
	rss 		string not null unique,
	added 		integer,
	rebuilt 	integer,
	modified 	integer,
	etag 		string
);

drop table if exists bookmark;
create table bookmark
(
	bookmark_id 	integer primary key autoincrement,
	user_id 	integer not null,
	feed_id 	integer not null,
	title 		string not null,
	created 	integer,
	stale 		boolean,
	unique (user_id, feed_id)
);

drop table if exists tag;
create table tag
(
	bookmark_id 	integer not null,
	tag		string not null,
	unique (bookmark_id, tag)
);
