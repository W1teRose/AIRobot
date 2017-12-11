import numpy as np
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import normalize
import glob
import CNN_utils as cnn
import pickle
import time
import datetime
import functools
import scipy.misc
np.set_printoptions(threshold=np.nan)

path = 'D:/Dokumente/Programmieren/RoboPen/UnitySimulation/AIRobot_Simulation/DataProcessing/traindata/pre/*.pickle'
file = glob.glob(path)
data = None
print(file)

for f in file:
	if data is None:
		print("loaded: " + f)
		data = pickle.load(open(f, "rb"))
		print("loaded: " + f)
		X = data[0]
		y = data[1]
	else:
		data = pickle.load(open(f, "rb"))
		X = np.concatenate((X, data[0]))
		y = np.concatenate((y, data[1]))

def normalize_data(data):
	data_min = data.min(axis=(1,2), keepdims=True)
	data_max = data.max(axis=(1,2), keepdims=True)
	return ((data - data_min)/(data_max - data_min))

def rezisePosMat(posmat):
	tmp_posmat = np.zeros((posmat.shape[0], 100, 100, 3))
	for i in range(posmat.shape[0]):
		tmp_posmat[i] = scipy.misc.imresize(posmat[i], (100, 100))
	return tmp_posmat

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

X_test, X_valid = np.array_split(X_test, 2)
y_test, y_valid = np.array_split(y_test, 2)

posmat_train = X_train[:,:,:,3:6]
X_train = X_train[:,:,:3]
X_train = normalize_data(X_train)
posmat_train = rezisePosMat(posmat_train)
posmat_train = normalize_data(posmat_train)

posmat_test = X_test[:,:,:,3:6]
posmat_test = rezisePosMat(posmat_test)
posmat_test = normalize_data(posmat_test)
X_test = X_test[:,:,:3]
X_test = normalize_data(X_test)

posmat_valid = X_valid[:,:,:,3:6]
posmat_valid = rezisePosMat(posmat_valid)
posmat_valid = normalize_data(posmat_valid)
X_valid = X_valid[:,:,:3]
X_valid = normalize_data(X_valid)

print("X train: " + str(X_train.shape))
print("y train: " + str(y_train.shape))
print("posmat train: " + str(posmat_train.shape))
print("X test: " + str(X_test.shape))
print("y test: " + str(y_test.shape))
print("posmat test: " + str(posmat_test.shape))
print("X valid: " + str(X_valid.shape))
print("y valid: " + str(y_valid.shape))
print("posmat valid: " + str(posmat_valid.shape))

print("sample: ")
print(X_train[5,:10,:10,1])
print(posmat_train[1,:,:,1])
print(y_train[5])

def accuracy(predictions, labels):
	return (100.0 * np.sum(np.argmax(predictions, 1) == np.argmax(labels, 1)) / predictions.shape[0])

#architecture of main path
filter_size1 = 3
num_filters1 = 64
filter_size2 = 3
num_filters2 = 64
#maxpool
filter_size3 = 3
num_filters3 = 128
filter_size4 = 3
num_filters4 = 128
#maxpool
filter_size5 = 3
num_filters5 = 256
filter_size6 = 3
num_filters6 = 256
#maxpool

#architecture of the position-matrix-path
posmat_filter_size1 = 3
posmat_num_filter1 = 32
posmat_filter_size2 = 3
posmat_num_filter2 = 32
#maxpool
posmat_filter_size3 = 3
posmat_num_filter3 = 64
posmat_filter_size4 = 3
posmat_num_filter4 = 64
#maxpool
posmat_filter_size5 = 3
posmat_num_filter5 = 128
posmat_filter_size6 = 3
posmat_num_filter6 = 128
#maxpool

#the fully connected layers
fc_size1 	 = 4096
fc_size2 	 = 4096
fc_size3 	 = 1000


image_width = 300
image_height = 300
image_depth = 3
posmat_width = 300
posmat_height = 300
posmat_depth = 3
num_lable = 8


epochs = 3000
start_learning_rate = 0.0001
batch_size = 16
keep_probability = 0.5

graph = tf.Graph()
with graph.as_default():
	tf_X_train = tf.placeholder(tf.float32, shape=[None, image_height, image_width, image_depth], name='X')
	tf_posmat_train = tf.placeholder(tf.float32, shape=[None, posmat_height, posmat_width, posmat_depth], name='posmat')
	tf_y_train = tf.placeholder(tf.float32, shape=[None, num_lable], name='y')
	tf_y_train_cls = tf.argmax(tf_y_train, dimension=1)
	keep_prob = tf.placeholder(tf.float32, name='keep_prob')

	global_step = tf.Variable(0, trainable=False)
	learning_rate = tf.train.exponential_decay(start_learning_rate, global_step, 1000, 0.96, staircase=True)
	print(tf_X_train)

	tf_images = tf.image.resize_images(tf_X_train, [224, 224])

	#the CNN Network split in stages
	with tf.name_scope('first_conv_stage_64_filter') as scope:
		layer_conv1, weights_conv1 = cnn.create_conv_layer(tf_images, image_depth, filter_size1, num_filters1, name='1_conv_layer')
		layer_conv2, weights_conv2 = cnn.create_conv_layer(layer_conv1, num_filters1, filter_size2, num_filters2, name='2_conv_layer')
		layer_conv2_pool = cnn.pooling(layer_conv2, name='layer_2_pooling')

	with tf.variable_scope('secound_conv_stage_128_filter') as scope:
		layer_conv3, weights_conv3 = cnn.create_conv_layer(layer_conv2_pool, num_filters2, filter_size3, num_filters3, name='3_conv_layer')
		layer_conv4, weights_conv4 = cnn.create_conv_layer(layer_conv3, num_filters3, filter_size4, num_filters4, name='4_conv_layer')
		layer_conv4_pool = cnn.pooling(layer_conv3, name='layer_4_pooling')

	with tf.variable_scope('third_conv_stage_256_filter') as scope:
		layer_conv5, weights_conv5 = cnn.create_conv_layer(layer_conv4_pool, num_filters4, filter_size5, num_filters5, name='5_conv_layer')
		layer_conv6, weights_conv6 = cnn.create_conv_layer(layer_conv5, num_filters5, filter_size6, num_filters6, name='6_conv_layer')
		layer_conv6_pool = cnn.pooling(layer_conv6, name='layer_6_pooling')


	#the position-matrix-path in stages
	with tf.name_scope('first_posmat_stage_32_filter') as scope:
		posmat_layer_conv1, posmat_weights_conv1 = cnn.create_conv_layer(tf_posmat_train, posmat_depth, posmat_filter_size1, posmat_num_filter1, name='1_posmat_conv_layer')
		posmat_layer_conv2, posmat_weights_conv2 = cnn.create_conv_layer(posmat_layer_conv1, posmat_num_filter1, posmat_filter_size2, posmat_num_filter2, name='2_posmat_conv_layer')
		posmat_layer_conv2_pool = cnn.pooling(posmat_layer_conv2, name='posmat_layer_2_pooling')

	with tf.name_scope('secound_posmat_stage_64_filter') as scope:
		posmat_layer_conv3, posmat_weights_conv3 = cnn.create_conv_layer(posmat_layer_conv2_pool, posmat_num_filter2, posmat_filter_size3, posmat_num_filter3, name='3_posmat_conv_layer')
		posmat_layer_conv4, posmat_weights_conv4 = cnn.create_conv_layer(posmat_layer_conv3, posmat_num_filter3, posmat_filter_size4, posmat_num_filter4, name='4_posmat_conv_layer')
		posmat_layer_conv4_pool = cnn.pooling(posmat_layer_conv4, name='posmat_layer_4_pooling')

	with tf.name_scope('secound_posmat_stage_128_filter') as scope:
		posmat_layer_conv5, posmat_weights_conv5 = cnn.create_conv_layer(posmat_layer_conv4_pool, posmat_num_filter4, posmat_filter_size5, posmat_num_filter5, name='5_posmat_conv_layer')
		posmat_layer_conv6, posmat_weights_conv6 = cnn.create_conv_layer(posmat_layer_conv5, posmat_num_filter5, posmat_filter_size6, posmat_num_filter6, name='6_posmat_conv_layer')
		posmat_layer_conv6_pool = cnn.pooling(posmat_layer_conv6, name='posmat_layer_6_pooling')

	with tf.variable_scope('fully_connected_layer') as scope:
		layer_flat, num_features = cnn.flatten_layer(layer_conv6_pool, name='flatten_layer')
		posmat_layer_flat, posmat_num_features = cnn.flatten_layer(posmat_layer_conv6_pool, name='flatten_posmat_layer')
		concat_posmat_main = tf.concat([layer_flat, posmat_layer_flat], 1)
		fc_layer1 = cnn.create_fully_connected_layer(concat_posmat_main, (num_features + posmat_num_features), fc_size1, name='1_fully_connected')
		fc_layer1_dropout = cnn.dropout(fc_layer1, keep_prob, name='1_layer_dropout')
		fc_layer2 = cnn.create_fully_connected_layer(fc_layer1_dropout, fc_size1, fc_size2, name='2_fully_connected')
		fc_layer2_dropout = cnn.dropout(fc_layer2, keep_prob, name='2_layer_dropout')
		fc_layer3 = cnn.create_fully_connected_layer(fc_layer2_dropout, fc_size2, fc_size3, name='3_fully_connected')
		fc_layer4 = cnn.create_fully_connected_layer(fc_layer3, fc_size3, num_lable, relu=False, name='4_fully_connected')


	y_pred = tf.nn.softmax(fc_layer4)
	y_pred_cls = tf.argmax(y_pred, dimension=1)
	cross_entropy = tf.nn.sigmoid_cross_entropy_with_logits(logits=fc_layer4, labels=tf_y_train)
	cost = tf.reduce_mean(cross_entropy)
	optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate).minimize(cost, global_step=global_step)
	correct_prediction = tf.equal(y_pred_cls, tf_y_train_cls)
	accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))

	tf.summary.scalar('Accuracy', accuracy)
	tf.summary.scalar('loss/cost', cost)
	merged = tf.summary.merge_all()
	saver = tf.train.Saver()


tf.reset_default_graph()
with tf.Session(graph=graph) as session:
	tf.global_variables_initializer().run()
	train_writer = tf.summary.FileWriter('statistics/train', session.graph)
	total_epochs = 1
	courent_batch_position = 0


	for i in range(epochs):
		if (courent_batch_position + batch_size) <= X_train.shape[0]:
			nextBatchPosition = (courent_batch_position+batch_size)
			X_batch = X_train[courent_batch_position : nextBatchPosition,...]
			y_batch = y_train[courent_batch_position : nextBatchPosition,...]
			posmat_batch = posmat_train[courent_batch_position : nextBatchPosition,...]
			courent_batch_position += batch_size
		else:
			overLapp = ((courent_batch_position + batch_size) - X_train.shape[0])
			X_batch = X_train[: overLapp,...]
			y_batch = y_train[: overLapp,...]
			posmat_batch = posmat_train[: overLapp,...]
			courent_batch_position = overLapp

		session.run(optimizer, feed_dict={tf_X_train: X_batch, tf_y_train: y_batch, keep_prob: keep_probability})
		summary, acc = session.run([merged, accuracy], feed_dict={tf_X_train: X_batch, tf_y_train: y_batch, tf_posmat_train: posmat_batch, keep_prob: 1})
		train_writer.add_summary(summary, total_epochs)
		total_epochs += 1
		if total_epochs % 100 == 0:

			all_acc_valid = []
			courent_batch_position_valid = 0
			for i in range(int(X_valid.shape[0]/batch_size)+1):
				if (courent_batch_position_valid + batch_size) <= X_valid.shape[0]:
					nextBatchPosition_valid = (courent_batch_position_valid+batch_size)
					X_batch_valid = X_valid[courent_batch_position_valid : nextBatchPosition_valid,...]
					y_batch_valid = y_valid[courent_batch_position_valid : nextBatchPosition_valid,...]
					posmat_batch_valid = posmat_valid[courent_batch_position_valid : nextBatchPosition_valid,...]
					courent_batch_position_valid += batch_size
				else:
					overLapp_valid = ((courent_batch_position_valid + batch_size) - X_valid.shape[0])
					X_batch_valid = X_valid[: overLapp_valid,...]
					y_batch_valid = y_valid[: overLapp_valid,...]
					posmat_batch_valid = posmat_valid[: overLapp_valid,...]
					courent_batch_position_valid = overLapp_valid

				all_acc_valid.append(session.run(accuracy, feed_dict={tf_X_train: X_batch_valid, tf_y_train:y_batch_valid, tf_posmat_train: posmat_batch_valid, keep_prob: 1}))
			print("Valid Accuracy: " + str(functools.reduce(lambda x_, y_: x_ + y_, all_acc_valid)/len(all_acc_valid)))
			print("loss: " + str())

			print("epoch: {}; Train Accuracy: {}".format(total_epochs, acc))
			print("batches seen: " + str(tf.train.global_step(session, global_step)))

	save_path = saver.save(session, "model.ckpt")
	all_acc_test = []
	for i in range(int(X_test.shape[0]/batch_size)+1):
		if (courent_batch_position + batch_size) <= X_test.shape[0]:
			nextBatchPosition = (courent_batch_position+batch_size)
			X_batch = X_test[courent_batch_position : nextBatchPosition,...]
			y_batch = y_test[courent_batch_position : nextBatchPosition,...]
			posmat_batch = posmat_test[courent_batch_position : nextBatchPosition,...]
			courent_batch_position += batch_size
		else:
			overLapp = ((courent_batch_position + batch_size) - X_test.shape[0])
			X_batch = X_test[: overLapp,...]
			y_batch = y_test[: overLapp,...]
			posmat_batch = posmat_test[: overLapp,...]
			courent_batch_position = overLapp

	all_acc_test.append(session.run(accuracy, feed_dict={tf_X_train: X_batch, tf_y_train:y_batch, tf_posmat_train: posmat_batch, keep_prob: 1}))
	print("Test Accuracy: " + str(functools.reduce(lambda x, y: x + y, all_acc_test)/len(all_acc_test)))
	session.close()
