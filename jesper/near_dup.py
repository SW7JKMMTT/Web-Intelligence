#!/bin/env python
import sys
import hashlib
from pprint import pprint

available_hash_algorithms = list(hashlib.algorithms_available)

def makeShingle(shinkle_size, string):
    shanks = []
    for k,i in enumerate(range(len(string.split()))):
        shanks.append("")
        shanks[k] = ""
        shanks[k] += ' '.join(string.split()[i:i+shinkle_size])
    return shanks

def makeHash(shinkles, hash_alg):
    hashes = []
    for shinkle in shinkles:
        weed = hashlib.new(hash_alg)
        weed.update(shinkle.encode('utf-8'))
        hashes.append(weed.hexdigest())
    return hashes

def jaccard(shank_a, shank_b):
    overlap = set(shank_a).intersection(shank_b)
    union = set(shank_a).union(shank_b)

    jcrd = len(overlap) / len(union)
    print('Jaccard:', jcrd)
    return jcrd

def minHash(shinkles, num=available_hash_algorithms):
    return [min(makeHash(shinkles, n)) for n in num]

def sketch_compare(sketch_a, sketch_b):
    equal = 0
    for hash_pair in zip(sketch_a, sketch_b):
        if hash_pair[0] == hash_pair[1]:
            equal += 1
    return equal / len(sketch_a)

def near_dup_percentage(ssize, textA, textB):
    shinkles_a = makeShingle(ssize, textA)
    shinkles_b = makeShingle(ssize, textB)
    if len(textA) < 100:
        return jaccard(shinkles_a, shinkles_b)
    else:
        min_hashes_a = minHash(shinkles_a)
        min_hashes_b = minHash(shinkles_b)
        return sketch_compare(min_hashes_a, min_hashes_b)

if __name__ == '__main__':
    strings = (
        "Nulla lobortis iaculis mi nec eleifend. Aenean fringilla scelerisque mattis. Quisque tincidunt et dui vitae pellentesque. Maecenas nec placerat tortor, a mattis erat. Nam id laoreet metus. Maecenas malesuada sem nec tortor ullamcorper, ut tincidunt erat egestas. Quisque ac mi neque. Vivamus rutrum ac ipsum sed interdum. Nullam placerat, augue viverra laoreet auctor, ex lectus ultricies urna, at pharetra justo metus et lorem. Quisque vitae mattis nunc. Nullam eget malesuada erat, nec dapibus ligula. Cras malesuada leo a tortor tincidunt, nec convallis augue mollis. Proin scelerisque ultricies erat malesuada mattis. Quisque sollicitudin justo ut tempus ullamcorper. Donec quis metus quam.",
        "Nulla lobortis iaculis mi nec eleifend. Aenean fringilla memes mattis. Obama is a dank memer et dui vitae pellentesque. Maecenas nec placerat tortor, a mattis erat. Nam id laoreet metus. Maecenas malesuada sem nec tortor ullamcorper, ut tincidunt erat egestas. Quisque ac mi neque. Vivamus rutrum ac ipsum sed interdum. Nullam placerat, augue viverra laoreet auctor, ex lectus ultricies urna, at pharetra justo metus et lorem. Quisque vitae mattis nunc. Nullam eget malesuada erat, nec dapibus ligula. Cras malesuada leo a tortor tincidunt, nec convallis augue mollis. Proin scelerisque ultricies erat malesuada mattis. Quisque sollicitudin justo ut tempus ullamcorper. Donec quis metus quam."
    )
    print(near_dup_percentage(100, strings[0], strings[1]))
