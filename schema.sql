drop table if exists entries;
create table entries (
  id integer primary key autoincrement,
  original_url text not null,
  shorten_url text not null,
  faurls integer not null
);