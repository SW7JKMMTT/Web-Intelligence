import hashlib
import sys
from pprint import pprint


def string_to_shingles(stringle, shingle_length):
    stringle_array = stringle.split()

    return [" ".join(stringle_array[x:x + shingle_length]) for x in range(len(stringle_array))]


def jaccard(list1, list2):
    return len(set(list1).intersection(list2)) / len(set(list1).union(list2))


def string_to_hash(input_string, offset=0):
    hasher = hashlib.new(list(hashlib.algorithms_available)[offset])

    hasher.update(input_string.encode("latin-1"))

    return hasher.hexdigest()[:8]


def string_to_int(input_string, offset=0):
    return int(string_to_hash(input_string, offset), 16)


def list_of_string_to_list_of_ints(list_of_strings):
    return [string_to_int(x) for x in list_of_strings]


def detect_near_duplicates(a, b, shingle_length=2):
    a = string_to_shingles(a, shingle_length)
    b = string_to_shingles(b, shingle_length)

    return jaccard(list_of_string_to_list_of_ints(a), list_of_string_to_list_of_ints(b)) >= 0.9


if __name__ == "__main__":
    if len(sys.argv) == 2:
        pprint(detect_near_duplicates("Don't let your dreams be memes.", "Don't let your memes be dreams.", sys.argv[1]))
    else:
        pprint(detect_near_duplicates("Don't let your dreams be memes.", "Don't let your memes be dreams."))
