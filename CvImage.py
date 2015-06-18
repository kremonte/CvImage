import cv2
import inspect

cvSkipMethods = [
	'imread',
	'imreadmulti',
	'imshow',
	'imwrite',
	'imdecode',
	'imencode'
]

class CvImage:
	"""Chainable OpenCV image class. Wraps cv2 methods."""
	cvMethods = {}

	@staticmethod
	def getCvMethods(root, method_dict):
		for method_name, method in inspect.getmembers(root):
			if method_name in cvSkipMethods:
				continue
			elif inspect.ismodule(method):
				CvImage.getCvMethods(method, method_dict)
			elif callable(method) and method.__doc__:
				method_type = 'pass'
				method_ret = method.__doc__.split('->')[-1].strip()
				if method_ret == 'dst' or method_ret == 'img' or method_ret == '_dst':
					method_type = 'chainable'				
				else:
					ret_values = method_ret.split(',')
					if len(ret_values) > 1:
						if ret_values[-1].strip() == 'dst':
							method_type = 'data_chainable'

				if method_name in method_dict:
					method_name = '{}_{}'.format(root.__name__.split('.')[-1], method_name)

				method_dict[method_name] = (method_type, method)

	def __init__(self, *args, **kwargs):
		if CvImage.cvMethods == {}:
			CvImage.getCvMethods(cv2, self.cvMethods)

		if type(args[0]) is str:
			# initialize from a filename
			self.image = cv2.imread(*args)
		else:
			# initialize from np array
			self.image = args[0]

		if 'name' in kwargs:
			self.name = kwargs.name
		else:
			self.name = 'CvImage'

		# set dimensions (width, height, depth)
		shape = self.image.shape
		self.height = shape[0]
		self.width = shape[1]
		if len(shape) == 3:
			self.depth = shape[2]
		else:
			self.depth = 1

	def __repr__(self):
		return repr(self.image)

	def __getattr__(self, key):
		if key in CvImage.cvMethods:
			return self.wrapCvMethod(key)
		else:
			raise AttributeError(key)

	def __getitem__(self, key):
		return self.image[key]

	def __setitem__(self, key, val):
		self.image[key] = val

	def __delitem__(self, key):
		del self.image[key]

	def __cmp__(self, target):
		if hasattr(target, 'image'):
			return cmp(self.image, target.image)
		else:
			return cmp(self.image, target)

	def wrapCvMethod(self, key):
		method_type, method = CvImage.cvMethods[key]

		def wrapped(*args, **kwargs):
			if method_type == 'chainable':
				self.image = method(self.image, *args)
				return self
			elif method_type == 'data_chainable':
				ret = method(self.image, *args)
				self.data = ret[:-1]
				self.image = ret[-1]
				return self
			else:
				return method(self.image, *args)

		return wrapped

	def show(self, name = ''):
		cv2.imshow(name or self.name, self.image)
		return self

	def save(self, filename = ''):
		cv2.imwrite(filename or '{}.png'.format(self.name), self.image)
		return self

	def copy(self):
		return CvImage(self.image.copy())

	def crop(self, slices):
		for i, arg in enumerate(slices):
			if type(arg) is str:
				# percentage
				arg = int(arg[:-1]) / 100
				if i <= 1:
					arg *= self.height
				else:
					arg *= self.width
				slices[i] = arg

		self.image = self.image[slices[0]:slices[1], slices[2]:slices[3]]
		return self

	@staticmethod
	def kernel(ktype = 'ELLIPSE', size = (3,3)):
		key = 'MORPH_{}'.format(ktype.upper())
		return cv2.getStructuringElement(cv2[key], size)
