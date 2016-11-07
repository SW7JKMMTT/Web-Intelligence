import numpy as np
import pandas as pd
import scipy.stats as sp
import math
import begin
import sys
from pprint import pprint

def read_data(rating_file):
	ratings_cols = ['user_id', 'item_id', 'rating','timestamp']
	ratings_data = pd.read_csv(rating_file, names=ratings_cols, sep='\t', encoding='latin-1')
	print(ratings_data)
	#movie_cols = ['movie_id', 'title', 'release_date', 'video_release_date', 'imdb_url']
	#movie_data = pd.read_csv('ml-100k/u.item', names=movie_cols, sep='|', encoding='latin-1', usecols=range(5))
	#print(movie_data)

	return ratings_data

def pearson(u1, u2, ratings):
	u1_data = ratings.loc[ratings['user_id'] == u1]
	u2_data = ratings.loc[ratings['user_id'] == u2]
	res = pd.merge(u1_data, u2_data, on='item_id', how='inner')
	# TODO: Adjust for inaccuracy
	return np.max(sp.pearsonr(res.rating_x, res.rating_y))

def user_avg_rating(u1, ratings):
	return np.mean(ratings.loc[ratings['user_id'] == u1].rating)

def user_rating(u1, p, ratings):
	return ratings.loc[((ratings['user_id'] == u1) & (ratings['item_id'] == p))].rating.iloc[0]

def contribution_score(how_much_like_me, their_id, p, ratings):
	return how_much_like_me * (user_rating(their_id, p, ratings) - user_avg_rating(their_id, ratings))

def pred(a, p, ratings, k=20, threshold=0.666):
	a_avg_rating = user_avg_rating(a, ratings)
	#print(a_avg_rating)
	people_who_have_rated_p = ratings.loc[ratings['item_id'] == p].user_id
	#print(people_who_have_rated_p)
	pearson_res = [(pearson(a, u2, ratings), u2) for u2 in people_who_have_rated_p]
	filtered_pearson = filter(lambda x: not math.isnan(x[0]), pearson_res)
	sorted_pearson = sorted(filtered_pearson, reverse=True)
	k_top = [val for val in sorted_pearson[:k] if val[0] > threshold]
	#pprint(k_top)
	sum_sim = np.sum([k[0] for k in k_top])
	#pprint(sum_sim)
	contribution_from_each = [contribution_score(*k, p, ratings) / sum_sim for k in k_top]
	#pprint(contribution_from_each)
	res = a_avg_rating + np.sum(contribution_from_each)
	#print(res)
	return res

def test(ratings):
	actual_ratings = read_data('ml-100k/u1.test')
	our_predictions = np.empty((len(actual_ratings), 3))
	for i, rating in actual_ratings.iterrows():
		our_predictions[i] = [rating.user_id.astype('float'), rating.item_id.astype('float'), pred(rating.user_id.astype('float'), rating.item_id.astype('float'), ratings, k=7)]
		if i % 10 == 0:
			print(i, "/", len(actual_ratings))

@begin.start
def main(input_file:"Input rating file"='ml-100k/u1.base'):
	ratings = read_data(input_file)
	print(pred(1, 10, ratings))
	test(ratings)

