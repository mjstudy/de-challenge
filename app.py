import socket
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask_restx import Api
import os
from flask import request, jsonify
import requests
import json
from sqlalchemy.dialects.postgresql import ARRAY
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


# Initial Flask app settings
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
db = SQLAlchemy(app)
limiter = Limiter(key_func=get_remote_address)
limiter.init_app(app)


class CoinsModel(db.Model):
    """ Model class to map the dataset (fetched message) to backend table

    task_run column is the auto-incremented primary key column.
    exchanges and id columns are populated with the data fetched & received.
    db.create_all() creates the table corresponding to this model class.
    db.drop_all() drops the schema prior to the app boot-up.

    Schema re-creation logic can be externalized using cli with FlaskGroup
    """
    __tablename__ = 'coins'
    task_run = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id = db.Column(db.String(128), nullable=False)
    exchanges = db.Column(ARRAY(db.String), default=[])

    def __init__(self, id, exchanges):
        self.id = id
        self.exchanges = exchanges

    def to_dict(self):
        return dict(task_run=self.task_run, id=self.id, exchanges=self.exchanges)

# db.drop_all()
db.create_all()

def get_ticker_info(ticker_id):
    """Simple coin gecko call and dict construction
    """
    coin_gecko_url = "https://api.coingecko.com/api/v3/coins/{}/tickers".format(ticker_id)
    r = requests.get(coin_gecko_url)
    
    return json.loads(r.content.decode('utf-8')), r.status_code

 
@app.route("/coins", methods=["POST"])
@limiter.limit("15 per minute")
def coins_rest():
    """ Method which can accommodate REST logic as per the requirement.

    Currently, only POST HTTP verb is implemented (Create of CRUD) and it indicates a record
    creation in the backend postgresql table. This can be extended further for other HTTP verbs
    such as GET, PATCH or PUT to form a full CRUD app.

    Call from coin-spewer Rust application:
        cargo run -- -e http://localhost:5004/coins -r 10 -p 1 -d 1000
    """
    # checks for the content-type JSON and CSV
    # and constructs the list of ids to coins_list
    if request.content_type == "application/json":
        post_data = request.get_json()
        coins_list = list(set(post_data["coins"]))
    else:
        request_csv_data = request.data.decode("utf-8").split("\n")
        coins_list = list(set(request_csv_data[1:]))
    
    print("request content-type: {}. IDs: {}".format(request.content_type, str(coins_list)))

    # Once coins_list is constructed, iterate through each id to 
    # work on requirement logic
    for id in coins_list:
        # check if the coin ticker is already present.
        # if it's present, then skip from db storage
        coins_item = CoinsModel.query.filter_by(id=id).all()
        if not coins_item:
            # coinGecko call; collect response dict and code
            ticker_res, coin_geck_status_code = get_ticker_info(id)

            # 200 means coinGecko gives back valid exchange response to an id
            if coin_geck_status_code == 200:
                exchanges_list = []
                # collect only exchange info for each id
                for ticker in ticker_res["tickers"]:
                    exchanges_list.append(ticker["market"]["identifier"])

                # PostgreSQL data save operation
                # one row per id/coin
                db.session.add(CoinsModel(id=id, exchanges=list(set(exchanges_list))))
                db.session.commit()
                print("id saved: {}".format(id))
            else:
                print("coin gecko failure res: {}, id: {}".format(coin_geck_status_code, id))

    return jsonify({"message": "completed"})

    
if __name__ == '__main__':
    hostname = socket.gethostname()
    # serve(app, host=hostname, port=5000)
    app.run(debug=True, host=hostname, port=5000)

