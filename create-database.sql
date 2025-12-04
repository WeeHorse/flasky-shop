create table public.users
(
    id       serial
        primary key,
    name     varchar(80)  not null,
    password varchar(80)  not null,
    email    varchar(120) not null
        unique
);


create table public.vats
(
    id          serial
        constraint vats_pk
            primary key,
    region      text             not null,
    amount      double precision not null,
    description text             not null
);


create table public.product
(
    id       serial
        constraint product_pk
            primary key,
    name     varchar(80),
    price    numeric,
    stock    integer,
    currency text not null,
    vat      integer
        constraint product_vats_id_fk
            references public.vats
);

comment on column public.product.price is 'ex vat';


create table public.shopping_cart
(
    id         serial
        primary key,
    user_id    integer           not null
        references public.users
            on delete cascade,
    product_id integer           not null
        references public.product
            on delete cascade,
    amount     integer default 1 not null,
    constraint shopping_cart_uniq
        unique (user_id, product_id)
);