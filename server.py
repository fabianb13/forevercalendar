from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

if __name__ == '__main__':
    from ip_changer import ip_changer
    ip_changer.start()
    app.run(debug=False, host="0.0.0.0")
