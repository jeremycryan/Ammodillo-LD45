import math
import random

def normalize(vector, magnitude):
    r = math.sqrt(vector[0]**2 + vector[1]**2)
    if r == 0:
        vector[0] = magnitude
        vector[1] = 0
        return
    vector[0] *= magnitude/r
    vector[1] *= magnitude/r

def sign(n):
    return n/abs(n)

def list_subtraction(v1, v2):
    return [v1[0] - v2[0], v1[1] - v2[1]]

def list_addition(v1, v2):
    return [v1[0] + v2[0], v1[1] + v2[1]]

def magnitude(v):
    return math.sqrt(v[0]**2 + v[1]**2)

def dist_between(o1, o2):
    dx2 = (o1.x - o2.x)**2
    dy2 = (o1.y - o2.y)**2
    return math.sqrt(dx2 + dy2)

def dist_between_lists(v1, v2):
    dx2 = (v1[0] - v2[0])**2
    dy2 = (v1[1] - v2[1])**2
    return math.sqrt(dx2 + dy2)

def random_angle_vec():
    angle = random.random() * 2 * math.pi
    return angle_vec(angle)

def angle_vec(angle):
    return [1 * math.sin(angle), 1 * math.cos(angle)]