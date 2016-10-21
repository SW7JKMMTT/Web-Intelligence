import begin
from collections import *
import numpy as np
import pickle

class User(object):

    def __init__(self, name):
        self.name = name
        self.friends = set()
        self.summary = None
        self.review = None

    def __str__(self):
        return "{}: s {} r {}\n\t{}".format(self.name, self.summary, self.review, self.friends)

users = OrderedDict()
A = None
D = None

@begin.start
def main(file_path: "Path to data file" = None, pickle_path: "Pickled users and matrices" = None,  magic: "Enable magic" = False):
    global users
    global A
    global D
    if pickle_path:
        users, A, D, V= pickle.load(open(pickle_path, "rb"))
    else:
        pickle_path = "everything.pickle"
        assert isinstance(file_path, str)
        with open(file_path, "r") as data:
            new_user = None
            for line in data:
                line = line.lower()
                if "user:" in line:
                    new_user = User(line.split(':', 1)[1].strip())
                    users[new_user.name] = new_user
                elif "friends:" in line:
                    friends = line.split(":", 1)[1][1:-1].split("\t")
                    new_user.friends.update(friends)
                elif "summary:" in line:
                    new_user.summary = line.split(":", 1)[1]
                elif "review:" in line:
                    new_user.review = line.split(":", 1)[1]


        A = np.empty((len(users), len(users)), dtype= np.int8)
        D = np.empty((len(users), len(users)), dtype= np.int8)
        for i, user in enumerate(users.values()):
            print(i + 1, "/", len(users))
            D[i,i] = len(user.friends)
            for friend in user.friends:
                if friend in users.keys():
                    j = list(users.keys()).index(friend)
                    A[i,j] = 1

        L = D - A
        indexes = np.arange(A.shape[0])
        indexes.shape = (A.shape[0], 1)

        tmp_V = np.linalg.eig(L)[1][1,:]
        tmp_V.shape = (A.shape[0], 1)

        V = np.hstack((tmp_V, indexes))
        print(V)
        print(V.shape)
        pickle.dump((users, A, D, V), open(pickle_path, "wb"))

