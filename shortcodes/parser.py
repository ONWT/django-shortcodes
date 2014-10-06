import hashlib
import pprint
import re
import shortcodes.parsers
from django.core.cache import cache
from django.conf import settings


def import_parser(name):
	mod = __import__(name)
	components = name.split('.')
	for comp in components[1:]:
		mod = getattr(mod, comp)
	return mod


def construct_regex(parser_names):
		"""
		This regex is a modified version of wordpress origianl shortcode parser found here
		https://core.trac.wordpress.org/browser/trunk/src/wp-includes/shortcodes.php?rev=28413#L225

		'\['                              // Opening bracket
			'(\[?)'                           // 1: Optional second opening bracket for escaping shortcodes: [[tag]]
			"(parser_names)"                     // 2: Shortcode name
			'(?![\w-])'                       // Not followed by word character or hyphen
			'('                                // 3: Unroll the loop: Inside the opening shortcode tag
				'[^\]\/]*'                   // Not a closing bracket or forward slash
				'(?:'
					'\/(?!\])'               // A forward slash not followed by a closing bracket
					'[^\]\/]*'               // Not a closing bracket or forward slash
				')*?'
			')'
			'(?:'
				'(\/)'                        // 4: Self closing tag ...
				'\]'                          // ... and closing bracket
			'|'
				'\]'                          // Closing bracket
				'(?:'
					'('                        // 5: Unroll the loop: Optionally, anything between the opening and closing shortcode tags
						'[^\[]*'             // Not an opening bracket
						'(?:'
							'\[(?!\/\2\])' // An opening bracket not followed by the closing shortcode tag
							'[^\[]*'         // Not an opening bracket
						')*'
					')'
					'\[\/\2\]'             // Closing shortcode tag
				')?'
			')'
			'(\]?)'
		"""
		parser_names_reg = '|'.join(parser_names)
		return '\\[(\\[?)('+parser_names_reg+')(?![\\w-])([^\\]\\/]*(?:\\/(?!\\])[^\\]\\/]*)*?)(?:(\\/)\\]|\\](?:([^\\[]*(?:\\[(?!\\/\\2\\])[^\\\\[]*)*)\\[\\/\\2\\])?)(\\]?)'


def parse(value, parser_names=None):
	# TODO get these from config file
	if parser_names is None:
		parser_names = getattr(settings, 'SHORTCODES_PARSERS', ['youtube', 'vimo', 'tabs'])
	ex = re.compile(construct_regex(parser_names))
	groups = ex.finditer(value)
	pieces = {}
	parsed = value

	for item_match in groups:

		name = item_match.group(2)
		args = item_match.group(3)
		args = __parse_args__(args)
		content = item_match.group(5)
		#Content cleanup removed close tags in beginning
		contentcleanup = re.compile(r'^(<\/[^>]*>)+')
		content = contentcleanup.sub('', content)
		args["shortcodeContent"] = content

		length_diff = len(value)-len(parsed)

		#Ok so we strip the tags in front parsed content
		cleanup = re.compile(r'(<[^/][^>]*>)+$')
		start = cleanup.sub('', parsed[:item_match.start()-length_diff])
		parsed = start + parsed[item_match.start()-length_diff:]
		#and the at after content we strip closed
		endcleanup = re.compile(r'^(</[^>]*>)+')
		end = endcleanup.sub('', parsed[item_match.end()-length_diff:])
		parsed = parsed[:item_match.end()-length_diff] + end

		length_diff = len(value)-len(parsed)

		#item_match.group(0) returns the full match as string
		cachekey = hashlib.md5(item_match.group(0).encode('utf-8')).hexdigest()
		try:
			if cache.get(cachekey):
				parsed = parsed[:item_match.start()] + cache.get(cachekey) + parsed[item_match.end():]
			else:
				# TODO allow arbitrary modules to implement new parsers
				module = import_parser('shortcodes.parsers.' + name)
				function = getattr(module, 'parse')
				result = function(args)
				cache.set(cachekey, result, 3600)
				# using length difference of original text and parsed text to get offset of where to splice the text
				parsed = parsed[:item_match.start()-length_diff] + result + parsed[item_match.end()-length_diff:]
		except ImportError:
			pass
	return parsed


def __parse_args__(value):
	ex = re.compile(r'[ ]*(\w+)=([^" ]+|"[^"]*")[ ]*(?: |$)')
	groups = ex.findall(value)
	kwargs = {}

	for group in groups:
		if group.__len__() == 2:
			item_key = group[0]
			item_value = group[1]

			if item_value.startswith('"'):
				if item_value.endswith('"'):
					item_value = item_value[1:]
					item_value = item_value[:item_value.__len__() - 1]

			kwargs[item_key] = item_value

	return kwargs
