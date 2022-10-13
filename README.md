# de-challenge
### Stack:
* Flask
* PostgreSQL
* Docker and docker-compose

### Run
  
Recreate the runnable using docker-compose and start the app using `docker-compose up`. The `api` service and `api-db` service will become up and running. The api service gives an endpoint as `http://localhost:5004/coins` which can be take `POST` requests with content-type both `application/json` and `text/csv`.
```
cd de-challenge
docker-compose build
docker-compose up
```

run coin-spewer rust cli to call the API
```
cd de-challenge/coin-spewer/
cargo run -- -e http://localhost:5004/coins -r 10 -p 1 -d 1000
```

Use docker-compose to open a postgres shell
```
cd de-challenge/
docker-compose exec api-db psql -U postgres
```

Change the DB context and execute SQL query.
```
postgres=# \c challenge_db
challenge_db=# WITH coins_cte AS (
challenge_db(#     SELECT *,
challenge_db(#         UNNEST(exchanges) AS exchanges_unnest
challenge_db(#     FROM coins
challenge_db(# ) 
challenge_db-# SELECT DISTINCT exchanges_unnest
challenge_db-# FROM coins_cte
challenge_db-# WHERE exchanges_unnest LIKE '%x%'
challenge_db-# ;
 exchanges_unnest 
------------------
 dextrade
 bittrex
 wazirx
 coinex
 finexbox
 mxc
 stocks_exchange
 aex
(8 rows)
```
### docker-compose
docker-compose contains two services, one for the app/api and another for the db. Each service points to its own Dockerfile

### Backend table
* DB name: `challenge_db` (as per `db/schema.sql`)
* Table name:  [CoinsModel](https://github.com/mjstudy/de-challenge/blob/main/app.py#L22) model class in `app.py` contains the schema of `coins` table. `exchanges` columns is stored as `ARRAY` type.

### SQL challenge
Both SQL challenge queries are in [sql_challenge.sql](https://github.com/mjstudy/de-challenge/blob/main/sql_challenge.sql)

### Notes
* **Primary key in backend table:** currently, task_run column is the primary key with auto-increment feature. In production setting, if the requirement is to fail any attempt to insert duplicate `coin`/`id` record to the table, then physically setting a `UNIQUE` constraint or `composite primary key` would be ideal.
* **Throttling:** current quick implementation for rate-limit/throttling is by using flask_limiter package and applying the limit as a decorator to the route function. Once the request limit mentioned in the `@limiter.limit` decorator is reached, response code `429` will be generated from the API.
* **Exponential back-off**: CoinGecko gives `429` rate-limit response once its threshold is reached. The API can be coded to minimize the 429 from CoinGecko using an exponential back-off logic, but it will increase the overall response time to the end user PID (more than 400ms). So, such logic has not been implemented. 
* serve: Flask app is serving in dev/debug more for review. In production, we may use `WSGI` or `waitress.serve` to serve the app. 
