import math

PI = math.pi
TWOPI = 2.0 * PI

# main transformations

def getAnglesFromCartesian(x, y, lengthA=1, lengthB=1):
    ## check that the point is a valid option for these segment lengths
    
    d = math.sqrt(x**2 + y**2)
    minDist = abs(lengthA - lengthB)
    maxDist = abs(lengthA + lengthB)
    if not minDist <= d <= maxDist:
        raise UnreachablePointError(x=x, y=y, d=d, minDist=minDist, maxDist=maxDist)
    
    ## get one solution
    
    # theta_0 is the angle of the base segment, if the point were at (0, d)
    if d > 0:
        theta_0 = (PI / 2.0) - math.acos((d**2 + lengthA**2 - lengthB**2) /
                                         (2.0 * d * lengthA))
    else:
        theta_0 = 0
    # angleB is the angle of the second segment, relative to the base segment's rotation
    angleB = PI - theta_0 - math.acos((lengthA / lengthB) * math.cos(theta_0))
    # mu is the clockwise rotation angle to get from (0, d) to (x, y)
    mu = math.atan2(x, y)
    # angleA is the true angle of the base segment (theta_0 rotated clockwise by mu)
    angleA = theta_0 - mu
    # angleB stays the same after this mu rotation, since it was calculated relative
    # to the base segment's rotation

    ## to get the second solution, reflect the segments across the line from (0, 0)
    ## to (x, y) (the radial line)
    
    radialLineAngle = math.atan2(y, x)
    reflectedAngleA = radialLineAngle + (radialLineAngle - angleA)
    reflectedAngleB = -angleB
    
    return ((angleA, angleB), (reflectedAngleA, reflectedAngleB))

def getCartesianFromAngles(angleA, angleB, lengthA=1, lengthB=1):
    x = lengthA * math.cos(angleA) + lengthB * math.cos(angleA + angleB)
    y = lengthA * math.sin(angleA) + lengthB * math.sin(angleA + angleB)
    return x, y

# helpers

def getNearestAngleClone(angle, target):
    direction = 1 if angle < target else -1
    angleClone = angle
    while abs(angleClone - target) > PI:
        angleClone += direction * TWOPI
    return angleClone

class UnreachablePointError(Exception):
    def __init__(self, x, y, d, minDist, maxDist):
        errMsgTemplate = "Distance to ({}, {}) is {}. It must be between {} and {}."
        message = errMsgTemplate.format(x, y, d, minDist, maxDist)
        super(UnreachablePointError, self).__init__(message)
