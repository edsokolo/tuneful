import os
from tuneful import app

def run():
    port = int(os.environ.get('PORT', 8084))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    run()

