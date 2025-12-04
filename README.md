## `README.md`

# flasky-shop

A small demo webshop backend built with **Flask** and **SQLAlchemy**, using **PostgreSQL** as the database and **cookie-based sessions** for authentication.

The API exposes basic functionality for:

- User registration and login
- Listing and managing products
- A per-user shopping cart
- VAT definitions

---

## Requirements

- Python 3.10+ (earlier 3.x will probably work too)
- PostgreSQL 13+ (or compatible)
- `pip` for installing Python packages

Python packages used (install via `pip`):

- `Flask`
- `SQLAlchemy`
- `psycopg2-binary`
- `python-dotenv`


```bash
pip install Flask SQLAlchemy psycopg2-binary python-dotenv
```
---

## Configuration: `.env`

Configuration is read from environment variables using [`python-dotenv`](https://pypi.org/project/python-dotenv/).

Example file: `.env.example`

```env
# Copy this file to .env and fill in your local values

DB_HOST=localhost
DB_PORT=5432
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_DATABASE=my_app_db
```

### Steps

1. Copy the example file:

   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and set:

   * `DB_HOST` – host where PostgreSQL is running (often `localhost` or a container name)
   * `DB_PORT` – PostgreSQL port (default `5432`)
   * `DB_USER` – PostgreSQL username
   * `DB_PASSWORD` – PostgreSQL password
   * `DB_DATABASE` – database name for this app, e.g. `flasky_shop`

3. `main.py` loads the `.env` on startup:

   ```python
   from dotenv import load_dotenv
   load_dotenv()
   ```

   The values are used to construct the SQLAlchemy URL:

   ```python
   url = URL.create(
       drivername="postgresql+psycopg2",
       host=os.getenv("DB_HOST"),
       port=os.getenv("DB_PORT"),
       username=os.getenv("DB_USER"),
       password=os.getenv("DB_PASSWORD"),
       database=os.getenv("DB_DATABASE")
   )
   ```

---

## Database Setup

The project expects a PostgreSQL database with the schema defined in `create-database.sql`.

```sql
create table public.users
(
    id       serial primary key,
    name     varchar(80)  not null,
    password varchar(80)  not null,
    email    varchar(120) not null unique
);

create table public.vats
(
    id          serial primary key,
    region      text             not null,
    amount      double precision not null,
    description text             not null
);

create table public.product
(
    id       serial primary key,
    name     varchar(80),
    price    numeric,
    stock    integer,
    currency text not null,
    vat      integer references public.vats
);

comment on column public.product.price is 'ex vat';

create table public.shopping_cart
(
    id         serial primary key,
    user_id    integer not null references public.users on delete cascade,
    product_id integer not null references public.product on delete cascade,
    amount     integer default 1 not null,
    constraint shopping_cart_uniq unique (user_id, product_id)
);
```

### Steps

1. Create the database in PostgreSQL (name must match `DB_DATABASE` in `.env`):

   ```sql
   CREATE DATABASE flasky_shop;
   ```

2. Run the schema script:

   ```bash
   psql -h localhost -U your_db_user -d flasky_shop -f create-database.sql
   ```

3. (Optional) Insert some initial data (e.g. `vats` and `product` rows) using SQL or any DB tool.

> **Note:** In the given SQL, `product.currency` is `NOT NULL`, while the `/products` API currently only sets `name`, `price`, and `stock`. Depending on how you use the app, you may want to:
>
> * Add default values in the DB, or
> * Extend the API to also handle `currency` and `vat`.

---

## Running the Application

From the project root:

1. (Optional but recommended) Create and activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate      # on macOS/Linux
   # venv\Scripts\activate       # on Windows
   ```

2. Install dependencies (see above):

   ```bash
   pip install -r requirements.txt
   # or
   pip install Flask SQLAlchemy psycopg2-binary python-dotenv
   ```

3. Make sure `.env` is configured and the database is created.

4. Run the app:

   ```bash
   python main.py
   ```

By default Flask will run on:

```text
http://localhost:5000
```

---

## Authentication & Sessions

* Authentication is **session-based** using Flask’s signed cookies.
* Logging in via `POST /login` will set a session cookie in the client.
* Routes decorated with `@login_required` will only work if that cookie is sent.

In Postman:

* When you call `POST /login`, Postman will automatically store the session cookie.
* Subsequent requests to protected routes (within the same collection/environment and to the same host) will automatically include the cookie.

Protected routes (require login):

* `GET /users`
* `POST /products`
* `DELETE /products/<product_id>`
* `GET /cart`
* `POST /cart`
* `DELETE /cart`
* `GET /vats`
* `POST /vats`
* `PUT /vats/<vat_id>`

---

## REST API

Base URL (local):

```text
http://localhost:5000
```

### Users

#### `POST /users`

Create a new user.

* Auth: **Public**
* Body (JSON):

```json
{
  "name": "Alice",
  "email": "alice@example.com",
  "password": "secret123"
}
```

* Responses:

  * `201 Created` – user created successfully
  * `400 Bad Request` – missing required fields
  * `409 Conflict` – email already registered

#### `GET /users`

Get all users.

* Auth: **Requires login**
* Responses:

  * `200 OK` – list of users:

```json
[
  {
    "id": 1,
    "name": "Alice",
    "email": "alice@example.com"
  }
]
```

* `401 Unauthorized` – if not logged in

---

### Auth

#### `POST /login`

Log in with email and password.

* Auth: **Public**
* Body (JSON):

```json
{
  "email": "alice@example.com",
  "password": "secret123"
}
```

* Responses:

  * `200 OK` – login successful, session cookie set

```json
{
  "message": "Login successful.",
  "user": {
    "id": 1,
    "name": "Alice",
    "email": "alice@example.com"
  }
}
```

* `400 Bad Request` – missing email or password
* `401 Unauthorized` – invalid credentials

> Passwords are stored in **plaintext** in this demo. This should be changed to proper password hashing in any real-world use.

#### `GET /login`

Get the currently logged-in user (from session).

* Auth: **Requires active session**
* Responses:

  * `200 OK` – user info
  * `401 Unauthorized` – no user logged in or user not found (session is cleared)

#### `DELETE /login`

Log out (clear session).

* Auth: **Session-based**
* Response:

  * `200 OK` – session cleared

---

### Products

#### `GET /products`

List all products.

* Auth: **Public**
* Response:

  * `200 OK` – list of products:

```json
[
  {
    "id": 1,
    "name": "T-Shirt",
    "price": 199.0,
    "stock": 42,
    "currency": "SEK",
    "vat": 1
  }
]
```

#### `GET /products/<product_id>`

Get one product by ID.

* Auth: **Public**
* Path param:

  * `product_id` – integer
* Responses:

  * `200 OK` – product object
  * `404 Not Found` – if no product for that ID

#### `POST /products`

Create a new product.

* Auth: **Requires login**
* Body (JSON):

```json
{
  "name": "T-Shirt",
  "price": 199.0,
  "stock": 20
}
```

* Responses:

  * `201 Created`
  * `400 Bad Request` – if `name`, `price`, or `stock` missing

> The current implementation only stores `name`, `price`, and `stock` via SQL. Fields `currency` and `vat` in the DB schema are not yet handled by this API route.

#### `DELETE /products/<product_id>`

Delete a product by ID.

* Auth: **Requires login**
* Responses:

  * `200 OK` – product deleted (even if it didn’t exist)

---

### Shopping Cart

All cart operations require a logged-in user; the cart is tied to `session["user_id"]`.

#### `GET /cart`

Get the current user’s cart.

* Auth: **Requires login**
* Responses:

  * `200 OK` – list of cart items:

```json
[
  {
    "id": 1,
    "product_id": 1,
    "product_name": "T-Shirt",
    "price": 199.0,
    "stock": 20,
    "amount": 2,
    "total_price": 398.0
  }
]
```

#### `POST /cart`

Add items to the cart or increase quantity.

* Auth: **Requires login**
* Body (JSON):

```json
{
  "product_id": 1,
  "amount": 2
}
```

`amount` defaults to `1` if omitted.

* Behavior:

  * If the product is already in the cart, its `amount` is increased.
  * Otherwise, a new row is inserted.

* Responses:

  * `200 OK` – cart updated
  * `400 Bad Request` – missing or invalid `product_id` / `amount`
  * `404 Not Found` – product does not exist

#### `DELETE /cart`

Remove items from the cart or remove the product entirely.

* Auth: **Requires login**
* Body (JSON):

```json
{
  "product_id": 1,
  "amount": 1
}
```

`amount` defaults to `1` if omitted.

* Behavior:

  * If `amount` < current cart amount: decreases the amount.
  * If `amount` ≥ current cart amount: removes the row from `shopping_cart`.

* Responses:

  * `200 OK` – cart updated
  * `400 Bad Request` – missing or invalid `product_id` / `amount`
  * `404 Not Found` – product not in cart

---

### VAT (vats)

#### `GET /vats`

Get all VAT entries.

* Auth: **Requires login**
* Response:

  * `200 OK` – list of VAT definitions:

```json
[
  {
    "id": 1,
    "description": "Standard VAT",
    "amount": 0.25,
    "region": "SE"
  }
]
```

#### `POST /vats`

Create a VAT entry.

* Auth: **Requires login**
* Body (JSON):

```json
{
  "description": "Standard VAT",
  "amount": 0.25,
  "region": "SE"
}
```

* Responses:

  * `201 Created`
  * `400 Bad Request` – missing required fields

#### `PUT /vats/<vat_id>`

Update a VAT entry.

* Auth: **Requires login**
* Path param:

  * `vat_id` – integer
* Body (JSON):

```json
{
  "description": "Reduced VAT",
  "amount": 0.12,
  "region": "SE"
}
```

* Responses:

  * `201 Created` (note: uses 201 even though it’s an update)
  * `400 Bad Request` – missing required fields

---

## Postman Collection

You’ll find a ready-made Postman collection (no tests) in this repo.
Import it into Postman and set `{{base_url}}` to your API base (e.g. `http://localhost:5000`).

---
