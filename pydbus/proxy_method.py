from gi.repository import GLib
from .generic import bound_method
from .identifier import filter_identifier
from .timeout import timeout_to_glib
from .error import error_registration

try:
	from inspect import Signature, Parameter
	put_signature_in_doc = False
except:
	from ._inspect3 import Signature, Parameter
	put_signature_in_doc = True

class DBUSSignature(Signature):

	def __str__(self):
		result = []
		for param in self.parameters.values():
			p = param.name if not param.name.startswith("arg") else ""
			if type(param.annotation) == str:
				p += ":" + param.annotation
			result.append(p)

		rendered = '({})'.format(', '.join(result))

		if self.return_annotation is not Signature.empty:
			rendered += ' -> {}'.format(self.return_annotation)

		return rendered

class ProxyMethod(object):
	def __init__(self, iface_name, method):
		self._iface_name = iface_name
		self.__name__ = method.attrib["name"]
		self.__qualname__ = self._iface_name + "." + self.__name__

		self._inargs  = [(arg.attrib.get("name", ""), arg.attrib["type"]) for arg in method if arg.tag == "arg" and arg.attrib.get("direction", "in") == "in"]
		self._outargs = [arg.attrib["type"] for arg in method if arg.tag == "arg" and arg.attrib.get("direction", "in") == "out"]
		self._sinargs  = "(" + "".join(x[1] for x in self._inargs) + ")"
		self._soutargs = "(" + "".join(self._outargs) + ")"

		self_param = Parameter("self", Parameter.POSITIONAL_ONLY)
		pos_params = []
		for i, a in enumerate(self._inargs):
			name = filter_identifier(a[0])

			if not name:
				name = "arg" + str(i)

			param = Parameter(name, Parameter.POSITIONAL_ONLY, annotation=a[1])

			pos_params.append(param)
		ret_type = Signature.empty if len(self._outargs) == 0 else self._outargs[0] if len(self._outargs) == 1 else "(" + ", ".join(self._outargs) + ")"

		self.__signature__ = DBUSSignature([self_param] + pos_params, return_annotation=ret_type)

		if put_signature_in_doc:
			self.__doc__ = self.__name__ + str(self.__signature__)

	def __call__(self, instance, *args, **kwargs):
		argdiff = len(args) - len(self._inargs)
		if argdiff < 0:
			raise TypeError(self.__qualname__ + " missing {} required positional argument(s)".format(-argdiff))
		elif argdiff > 0:
			raise TypeError(self.__qualname__ + " takes {} positional argument(s) but {} was/were given".format(len(self._inargs), len(args)))

		# Python 2 sux
		for kwarg in kwargs:
			if kwarg not in ("timeout", "callback", "callback_args", "unpack_result", "pack_args"):
				raise TypeError(self.__qualname__ + " got an unexpected keyword argument '{}'".format(kwarg))
		timeout = kwargs.get("timeout", None)
		callback = kwargs.get("callback", None)
		callback_args = kwargs.get("callback_args", tuple())
		unpack_result = kwargs.get("unpack_result", True)
		pack_args = kwargs.get("pack_args", True)

		if pack_args:
			sinargs_variant = GLib.Variant(self._sinargs, args)
		elif not args:
			sinargs_variant = None
		else:
			sinargs_variant = args[0]

		call_args = (
			instance._bus_name,
			instance._path,
			self._iface_name,
			self.__name__,
			sinargs_variant,
			GLib.VariantType.new(self._soutargs),
			0,
			timeout_to_glib(timeout),
			None
		)

		if callback:
			call_args += (self._finish_async_call, (callback, callback_args, unpack_result))
			instance._bus.con.call(*call_args)
			return None

		else:
			result = None
			error = None

			try:
				result = instance._bus.con.call_sync(*call_args)
			except Exception as e:
				error = error_registration.transform_exception(e)

			if error:
				raise error

			if unpack_result:
				result = self._unpack_return(result)

			return result

	def _unpack_return(self, values):
		ret = values.unpack()
		if len(self._outargs) == 0:
			return None
		elif len(self._outargs) == 1:
			return ret[0]
		else:
			return ret

	def _finish_async_call(self, source, result_object, user_data):
		error = None
		result = None

		callback, callback_args, unpack_result = user_data

		try:
			result = source.call_finish(result_object)
		except Exception as err:
			error = error_registration.transform_exception(err)

		if not error and unpack_result:
			result = self._unpack_return(result)

		callback(*callback_args, returned=result, error=error)

	def __get__(self, instance, owner):
		if instance is None:
			return self

		return bound_method(self, instance)

	def __repr__(self):
		return "<function " + self.__qualname__ + " at 0x" + format(id(self), "x") + ">"
