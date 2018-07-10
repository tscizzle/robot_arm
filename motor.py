from time import sleep
import math
from threading import Thread
import RPi.GPIO as GPIO
from coordinates import (TWOPI,
                         getAnglesFromCartesian,
                         getCartesianFromAngles,
                         getNearestAngleClone,
                         UnreachablePointError)

# initialization

GPIO.setmode(GPIO.BOARD)

MOTOR_A = {
    'name': 'Motor A',
    'pins': {
        'pink': 7,
        'orange': 11,
        'blue': 16,
        'yellow': 18,
        'enable': 12
    },
    'state': {
        'currentPosition': 0,
        'currentSteps': 0
    }
}
MOTOR_B = {
    'name': 'Motor B',
    'pins': {
        'pink': 21,
        'orange': 23,
        'blue': 26,
        'yellow': 29,
        'enable': 31
    },
    'state': {
        'currentPosition': 0,
        'currentSteps': 256
    }
}
MOTORS = [MOTOR_A, MOTOR_B]

def setup():
    for motor in MOTORS:
        for pin in motor['pins'].values():
            GPIO.setup(pin, GPIO.OUT)
        GPIO.output(motor['pins']['enable'], 1)

# control

STEPS_PER_REVOLUTION = 513.0

POSITION_SETTINGS = [
    [1, 0, 1, 0],
    [0, 1, 1, 0],
    [0, 1, 0, 1],
    [1, 0, 0, 1],
]

def setStep(motor, settings):
    GPIO.output(motor['pins']['pink'], settings[0])
    GPIO.output(motor['pins']['orange'], settings[1])
    GPIO.output(motor['pins']['blue'], settings[2])
    GPIO.output(motor['pins']['yellow'], settings[3])

def letGo(motor):
    setStep(motor, [0, 0, 0, 0])

def rotate(motor, steps, delay):
    # build list of positions to go through
    direction = 1 if steps > 0 else -1
    position = motor['state']['currentPosition']
    positionsToSet = []
    stepsLeft = steps
    while stepsLeft:
        position = (position + direction) % len(POSITION_SETTINGS)
        positionsToSet.append(position)
        stepsLeft -= direction
    # go to each position listed
    for position in positionsToSet:
        settings = POSITION_SETTINGS[position]
        setStep(motor, settings)
        motor['state']['currentPosition'] = position
        motor['state']['currentSteps'] += direction
        sleep(delay / 1000.0)

def getDelays(stepsA, stepsB, fastDelay=20):
    # choose a delay for each motor so they finish at the same time
    if stepsA == 0 or stepsB == 0:
        return fastDelay, fastDelay
    stepsA, stepsB = abs(stepsA), abs(stepsB)
    MAX_DELAY = 100
    stepsRatio = float(max(stepsA, stepsB)) / float(min(stepsA, stepsB))
    slowDelay = stepsRatio * fastDelay
    delayA, delayB = ((slowDelay, fastDelay) if stepsA < stepsB else
                      (fastDelay, slowDelay))
    delayA, delayB = min(delayA, MAX_DELAY), min(delayB, MAX_DELAY)
    return delayA, delayB

def moveArm(stepsA, stepsB):
    # rotate each motor simultaneously, and return once they both finish
    delayA, delayB = getDelays(stepsA, stepsB)
    threadA = Thread(target=rotate, args=(MOTOR_A, stepsA, delayA))
    threadB = Thread(target=rotate, args=(MOTOR_B, stepsB, delayB))
    for thread in [threadA, threadB]:
        thread.start()
    for thread in [threadA, threadB]:
        thread.join()

def moveArmTo(targetX, targetY):
    ## calculate the number of steps to rotate each motor

    # get the two possible solutions for motor angles
    try:
        candidateAngles0, candidateAngles1 = getAnglesFromCartesian(targetX, targetY)
    except UnreachablePointError:
        return False
    # choose the solution that is faster to reach
    motorACurrentAngle = getAngleFromSteps(MOTOR_A['state']['currentSteps'])
    motorBCurrentAngle = getAngleFromSteps(MOTOR_B['state']['currentSteps'])
    bestCandidate = None
    bestBottleneck = None
    for angleA, angleB in [candidateAngles0, candidateAngles1]:
        candidateAngleA = getNearestAngleClone(angleA, motorACurrentAngle)
        candidateAngleB = getNearestAngleClone(angleB, motorBCurrentAngle)
        angleDistA = abs(candidateAngleA - motorACurrentAngle)
        angleDistB = abs(candidateAngleB - motorBCurrentAngle)
        bottleneck = max(angleDistA, angleDistB)
        if bestCandidate is None or bottleneck < bestBottleneck:
            bestCandidate = (candidateAngleA, candidateAngleB)
            bestBottleneck = bottleneck
    targetAngleA, targetAngleB = bestCandidate
    # from the target angles, get the number of steps to rotate each motor
    targetStepsA = getStepsFromAngle(targetAngleA)
    targetStepsB = getStepsFromAngle(targetAngleB)
    actualStepsA, actualStepsB = int(targetStepsA), int(targetStepsB)
    stepsA = actualStepsA - MOTOR_A['state']['currentSteps']
    stepsB = actualStepsB - MOTOR_B['state']['currentSteps']
    
    ## move the arm
    
    moveArm(stepsA, stepsB)
    
    ## keep track of where we actually went, given rounding
    
    actualAngleA = getAngleFromSteps(actualStepsA)
    actualAngleB = getAngleFromSteps(actualStepsB)
    actualX, actualY = getCartesianFromAngles(actualAngleA, actualAngleB)
    
    return actualX, actualY

def getStepsFromAngle(angle):
    steps = (angle / TWOPI) * STEPS_PER_REVOLUTION
    return steps

def getAngleFromSteps(steps):
    angle = (steps / STEPS_PER_REVOLUTION) * TWOPI
    return angle

def done():
    for motor in MOTORS:
        letGo(motor)
    GPIO.cleanup()

if __name__ == '__main__':
    setup()
