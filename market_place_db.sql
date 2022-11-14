create database marketplace_db;a

create table products_categories
(
    id            serial
        primary key,
    category_name varchar(255) not null
);

alter table products_categories
    owner to postgres;

create table users_categories
(
    id            serial
        primary key,
    category_name varchar(255) not null
);

alter table users_categories
    owner to postgres;

create table products
(
    id            serial
        primary key,
    product_name  varchar(255) not null
        constraint products_product_name_check
            check (length((product_name)::text) > 0),
    price         integer      not null
        constraint products_price_check
            check (price > 0),
    text_info     text         not null,
    image_path    text    default '/static/media/default.png'::text,
    category      integer
        constraint fk_category
            references products_categories
            on update cascade on delete cascade,
    count_product integer default 0
);

alter table products
    owner to postgres;

create table users
(
    id       serial
        primary key,
    email    varchar(255)
        unique
        constraint users_email_check
            check (length((email)::text) > 5),
    password varchar(255)
        constraint users_password_check
            check (length((password)::text) >= 8),
    category integer default 2
        constraint fk_category
            references users_categories
            on update cascade on delete cascade,
    profile  varchar
);

alter table users
    owner to postgres;

create table orders
(
    id           serial
        primary key,
    user_id      integer   not null
        constraint fk_user_id
            references users,
    sum_products integer   not null
        constraint orders_sum_check
            check (sum_products > 0),
    time_now     timestamp not null,
    address      text,
    number_order integer   not null
        unique
);

alter table orders
    owner to postgres;

create table products_ordered
(
    order_id      integer not null
        constraint fk_order_id
            references orders,
    product_id    integer not null
        constraint fk_product_id
            references products,
    count_product integer not null
);

alter table products_ordered
    owner to postgres;
