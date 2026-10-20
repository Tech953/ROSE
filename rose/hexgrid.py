"""Axial coordinates: six physical neighbors, cube lines, bounded BFS routes."""
from collections import deque

DIRS = ((1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1))


def key(pos):
    return f'{pos[0]},{pos[1]}'


def distance(a, b=(0, 0)):
    q, r = a[0] - b[0], a[1] - b[1]
    return max(abs(q), abs(r), abs(q + r))


def neighbors(pos):
    return [[pos[0] + q, pos[1] + r] for q, r in DIRS]


def disk(radius):
    return [[q, r] for q in range(-radius, radius + 1)
            for r in range(max(-radius, -q - radius), min(radius, -q + radius) + 1)]


def rounded(q, r):
    s = -q - r
    a, b, c = round(q), round(r), round(s)
    errors = abs(a - q), abs(b - r), abs(c - s)
    if errors[0] > errors[1] and errors[0] > errors[2]:
        a = -b - c
    elif errors[1] > errors[2]:
        b = -a - c
    return [a, b]


def line(a, b):
    n = distance(a, b)
    if n == 0:
        return [list(a)]
    return [rounded(a[0] + (b[0] - a[0]) * i / n + 1e-6,
                    a[1] + (b[1] - a[1]) * i / n + 1e-6) for i in range(n + 1)]


def path(tiles, start, goal, occupied=()):
    start, goal = key(start), key(goal)
    blocked = {key(p) for p in occupied} - {start}
    if goal not in tiles or not tiles[goal]['passable'] or goal in blocked:
        return None
    parents = {start: None}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        if current == goal:
            route = []
            while current is not None:
                route.append([int(x) for x in current.split(',')])
                current = parents[current]
            return route[::-1]
        for pos in neighbors([int(x) for x in current.split(',')]):
            nxt = key(pos)
            if nxt in tiles and tiles[nxt]['passable'] and nxt not in parents and nxt not in blocked:
                parents[nxt] = current
                queue.append(nxt)
    return None


def visible(tiles, start, goal):
    return all(key(p) in tiles and not tiles[key(p)].get('opaque', False)
               for p in line(start, goal)[1:-1])


def parse(value):
    try:
        values = value.split(',')
        if len(values) != 2 or any(len(v) > 4 for v in values):
            raise ValueError()
        return [int(v) for v in values]
    except (ValueError, AttributeError):
        raise ValueError('Use an axial hex coordinate, for example 1,-1.') from None
