import sys
import hashlib
from pprint import pprint

strings = (
    "Nulla lobortis iaculis mi nec eleifend. Aenean fringilla scelerisque mattis. Quisque tincidunt et dui vitae pellentesque. Maecenas nec placerat tortor, a mattis erat. Nam id laoreet metus. Maecenas malesuada sem nec tortor ullamcorper, ut tincidunt erat egestas. Quisque ac mi neque. Vivamus rutrum ac ipsum sed interdum. Nullam placerat, augue viverra laoreet auctor, ex lectus ultricies urna, at pharetra justo metus et lorem. Quisque vitae mattis nunc. Nullam eget malesuada erat, nec dapibus ligula. Cras malesuada leo a tortor tincidunt, nec convallis augue mollis. Proin scelerisque ultricies erat malesuada mattis. Quisque sollicitudin justo ut tempus ullamcorper. Donec quis metus quam.",
    "Nulla lobortis iaculis mi nec eleifend. Aenean fringilla memes mattis. Obama is a dank memer et dui vitae pellentesque. Maecenas nec placerat tortor, a mattis erat. Nam id laoreet metus. Maecenas malesuada sem nec tortor ullamcorper, ut tincidunt erat egestas. Quisque ac mi neque. Vivamus rutrum ac ipsum sed interdum. Nullam placerat, augue viverra laoreet auctor, ex lectus ultricies urna, at pharetra justo metus et lorem. Quisque vitae mattis nunc. Nullam eget malesuada erat, nec dapibus ligula. Cras malesuada leo a tortor tincidunt, nec convallis augue mollis. Proin scelerisque ultricies erat malesuada mattis. Quisque sollicitudin justo ut tempus ullamcorper. Donec quis metus quam."
)

def shinklefy(shinkle_size, string):
    shanks = []
    for k,i in enumerate(range(len(string.split()))):
        shanks.append("")
        shanks[k] = ""
        shanks[k] += ' '.join(string.split()[i:i+shinkle_size])
    return shanks

def blaze_it(shinkles, hash_no=0):
    hashes = []
    for shinkle in shinkles:
        weed = hashlib.new(list(hashlib.algorithms_available)[hash_no])
        weed.update(shinkle.encode('utf-8'))
        hashes.append(weed.hexdigest())
    return hashes

def jaccard(shank_a, shank_b):
    overlap = set(shank_a).intersection(shank_b)
    union = set(shank_a).union(shank_b)

    jcrd = len(overlap) / len(union)
    print('Jaccard:', jcrd)
    return jcrd

def weed_overload(shinkles, num=len(list(hashlib.algorithms_available))):
    return [min(blaze_it(shinkles, n)) for n in range(num)]

def sketch_compare(sketch_a, sketch_b):
    equal = 0
    for hash_pair in zip(sketch_a, sketch_b):
        if hash_pair[0] == hash_pair[1]:
            equal += 1
    return equal / len(sketch_a)

if __name__ == '__main__':
    shinkles_a = shinklefy(int(sys.argv[1]), strings[0])
    shinkles_b = shinklefy(int(sys.argv[1]), strings[1])
    jaccard(shinkles_a, shinkles_b)
    hashes_a = blaze_it(shinkles_a)
    hashes_b = blaze_it(shinkles_b)
    jaccard(hashes_a, hashes_b)
    min_hashes_a = weed_overload(shinkles_a)
    min_hashes_b = weed_overload(shinkles_b)
    print(sketch_compare(min_hashes_a, min_hashes_b))

