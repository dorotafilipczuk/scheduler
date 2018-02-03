from flask import Flask, Response


app = Flask(__name__)


@app.route('/')
def index():
    return Response(response='1661450931', status=200)


@app.route('/callback')
def google_auth_callback():
    """
    Route used by google to authenticate a user
    """
    pass

if __name__ == '__main__':
    app.run()
