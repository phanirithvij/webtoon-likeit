import json
import sys

import numpy as np
import numpy.ma as ma
from matplotlib import pyplot as plt


def plot_likes(filename):
    with open(filename, 'r') as j:
        data = json.load(j)

    x = np.array([p['i'] for p in data])
    y = np.array([p['c'] for p in data])
    e = np.array([not p['e'] for p in data])

    # https://stackoverflow.com/a/51913152/8608146
    x = ma.array(x)
    y = ma.array(y, mask=e)

    # TODO names in labels
    plt.plot(x, y.data, label=f'{filename}-free')
    plt.plot(x, y, label=f'{filename}-paid')
    # https://stackoverflow.com/a/22642641/8608146
    # plt.xlim(0, len(x))
    # plt.ylim(0, np.max(y))


if __name__ == '__main__':
    for x in sys.argv[1:]:
        plot_likes(x)
    plt.xlabel('Chapter #')
    plt.ylabel('Likes')
    plt.ylim(bottom=0)
    plt.legend()
    plt.show()
