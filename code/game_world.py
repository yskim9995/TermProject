
world = [[], [], []] # layers for game objects

def add_object(o, depth):
    world[depth].append(o)

def add_objects(ol, depth):
    world[depth] += ol

def remove_object(o):
    for layer in world:
        if o in layer:
            layer.remove(o)
            return

    raise Exception("World 에 존재하지 않는 오브젝트를 지우려고 시도함")


def update(dt):
    # 1. 모든 객체 업데이트 (이 부분은 원래 정상이었습니다)
    for layer in world:
        for o in layer:
            o.update(dt)


def render():
    for layer in world:
        for o in layer:
            o.draw()


