__author__ = 'Noobs'
import re
from django.template import Template, Context
from django.template.loader import render_to_string
from django.conf import settings
from shortcodes.parser import construct_regex, __parse_args__


def parse(kwargs, template_name="shortcodes/tabs.html"):
		Tabs_id = kwargs.get('id')
		Tab_Content = kwargs.get('shortcodeContent')
		if Tabs_id:
				ex = re.compile(construct_regex(['tab']))
				groups = ex.findall(Tab_Content)
				tabs = {}
				tabcount = 0
				for tab in groups:
						args = __parse_args__(args)
						title = args['title']
						tab_id = Tabs_id + tabcount
						tabs[title] = (tab_id, title, tab[5])

				ctx = {
					'tab_id': Tabs_id,
					'tabs': tabs
				}
				return render_to_string(template_name, ctx)
