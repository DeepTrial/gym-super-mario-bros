from gym_super_mario_bros import SuperMarioBrosEnv
import tqdm
import numpy as np
import cv2


env = SuperMarioBrosEnv()



print("TEST for normal usage:")
done = True
try:
    for _ in tqdm.tqdm(range(5000)):
        if done:
            state = env.reset()
            done = False
        else:
            state, reward, done, info = env.step(env.action_space.sample())
except KeyboardInterrupt:
    pass


print("TEST for tile and reshape operation:")
def resize(image):
    resized=cv2.resize(image,(84,84),interpolation=cv2.INTER_NEAREST)
    resized=np.round((resized))
    return resized
done=True
try:
    for index in tqdm.tqdm(range(5000)):
        if done:
            state = env.reset()
            done = False
        else:
            state, reward, done, info = env.step(env.action_space.sample())
            tile=resize(info["tile"])
except KeyboardInterrupt:
    pass