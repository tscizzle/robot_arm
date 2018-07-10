from time import sleep
from datetime import datetime
from dateutil.parser import parse as dateParse
import pytz
from threading import Thread
from flask import Flask, request, render_template
from motor import setup, done, moveArmTo
setup()

# flask app handles requests to update state

app = Flask(__name__)

state = {
    'currentCoordinates': [0, 0],
    'controller': {
        'lastRequest': '1970-01-01T00:00:00Z',
        'pressedKeys': [],
    },
    'done': False,
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/keyevent', methods=['POST'])
def keyevent():
    body = request.get_json()
    requiredFields = ['requestTime', 'pressedKeys']
    if all(field in body for field in requiredFields):
        requestTimeStr = body['requestTime']
        pressedKeysDict = body['pressedKeys']
        pressedKeys = [int(k) for k in pressedKeysDict]
        requestTime = dateParse(requestTimeStr)
        lastRequest = dateParse(state['controller']['lastRequest'])
        if requestTime > lastRequest:
            ALLOWED_KEYS = set([32, 37, 38, 39, 40])
            allowedPressedKeys = list(ALLOWED_KEYS & set(pressedKeys))
            state['controller']['pressedKeys'] = allowedPressedKeys
            state['controller']['lastRequest'] = requestTimeStr
    return ''

# a loop constantly checks the current state and acts accordingly

def controllerLoop():
    while True:
        if state['done']:
            done()
            break
        now = datetime.now(pytz.utc)
        parsedLastRequest = dateParse(state['controller']['lastRequest'])
        dormant = (now - parsedLastRequest).seconds >= 2
        if not dormant:
            pressedKeys = state['controller']['pressedKeys']
            SPACEBAR = 32
            LEFT = 37
            UP = 38
            RIGHT = 39
            DOWN = 40
            if SPACEBAR in pressedKeys:
                state['done'] = True
            elif any(key in pressedKeys for key in [LEFT, UP, RIGHT, DOWN]):
                UNIT = 0.05
                targetX, targetY = state['currentCoordinates']
                if LEFT in pressedKeys:
                    targetX -= UNIT
                if UP in pressedKeys:
                    targetY += UNIT
                if RIGHT in pressedKeys:
                    targetX += UNIT
                if DOWN in pressedKeys:
                    targetY -= UNIT
                moved = moveArmTo(targetX, targetY)
                if moved:
                    state['currentCoordinates'] = [targetX, targetY]
        else:
            sleep(0.1)

controllerThread = Thread(target=controllerLoop)
controllerThread.start()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', use_reloader=False)
    state['done'] = True
    controllerThread.join()
    
    
