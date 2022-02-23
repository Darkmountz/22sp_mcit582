import math


def num_BTC(b):
    reward = 50.0
    limit = 210000
    total_reward = 0.0

    if b > limit:
        while b > limit:
            total_reward += reward * limit
            b -= limit
            reward /= 2
        total_reward += reward * b
    else:
        total_reward = reward * b

    return total_reward
