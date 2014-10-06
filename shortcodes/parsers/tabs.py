__author__ = 'Noobs'
import re
import uuid
from django.template import Template, Context
from django.template.loader import render_to_string
from django.conf import settings
from shortcodes.parser import construct_regex, __parse_args__


def parse(kwargs, template_name="shortcodes/tabs.html"):
		Tabs_id = kwargs.get('id')
		Tab_Content = kwargs.get('shortcodeContent')
		tabs = []

		if not Tabs_id:
				Tabs_id = "Tab"+str(uuid.uuid4())
		if Tab_Content:
				ex = re.compile(construct_regex(['tab']))
				groups = ex.findall(Tab_Content)
				tabcount = 0
				for tab in groups:
						args = __parse_args__(tab[2])

						title = args['title']
						tab_id = Tabs_id + str(tabcount)
						tabs.append((tab_id, title, tab[4]))
						tabcount += 1

		ctx = {
			'tab_id': Tabs_id,
			'tabs': tabs
		}
		return render_to_string(template_name, ctx)
