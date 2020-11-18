import re
import scrapy
from scrapy.loader import ItemLoader
from chalcogenide_searcher.items import ChalcogenideData

def striptags(string):
	p = re.compile(r'<.*?>')
	return p.sub('', string)


class ChalcogenideRetriever(scrapy.Spider):
	name = 'chalcogenide_searcher'
	subpage_data = {'1': 'Thermo-Gas', '2': 'Thermo-Condensed', '4': 'Thermo-Phase', '0': 'Ion-Energetics'}
	
	def start_requests(self):
		readfile = open('element_symbols.txt')
		symbols = readfile.readlines()
		readfile.close()

		searchkeys = ['S', 'Se', 'Te']
		urls = []
		base_url = 'https://webbook.nist.gov/cgi/cbook.cgi?Formula=@&NoIon=on&Units=SI'
		
		alloys = []
		# binary alloys
		for key in searchkeys:
			for symbol in symbols:
				alloys.append('{}?{}?'.format(key, symbol.strip()))

		# ternary alloys
		ternary_alloys = []
		for alloy in alloys:
			for symbol in symbols:
				ternary_alloys.append('{}{}?'.format(alloy, symbol.strip()))

		alloys += ternary_alloys

		for alloy in alloys:
			urls.append(base_url.replace('@', '{}'.format(alloy)))

		for search_url in urls:
			yield scrapy.Request(search_url, self.parse)

	def parse(self, response):
		search_results = response.xpath('//ol/li/a/@href').getall()

		for result in search_results:
			yield response.follow(response.urljoin(result), self.parse_result)

	def parse_result(self, response):
		loader = ItemLoader(item=ChalcogenideData(), selector=response)
		loader.add_css('Chalcogenide_Name', 'title::text')
		chalcogenide_formula = striptags(response.css('li')[14].get())[9:]
		loader.add_value('Chalcogenide_Formula', chalcogenide_formula)
		chalcogenide_data = loader.load_item()

		subpages = ['1', '2', '4', '20']
		subpage_extension = '&Mask=@'

		for subpage_num in subpages:
			yield scrapy.Request(response.url + subpage_extension.replace('@', subpage_num), callback=self.parse_data, meta={'chalcogenide_data': chalcogenide_data})

	def parse_data(self, response):
		chalcogenide_data = response.meta['chalcogenide_data']
		loader = ItemLoader(item=chalcogenide_data, response=response)

		category_data = []
		subpage_id = response.url[-1]

		if response.css('table.data'):
			for tablerow in response.css('table.data')[0].css('tr'):
				if tablerow.css('td'):
					row_data = {}

					row_data['Quantity'] = striptags(tablerow.css('td')[0].get()).replace('\u00b0', '^')
					row_data['Value'] = striptags(tablerow.css('td')[1].get()).replace('\u00b1', '+-')
					row_data['Units'] = striptags(tablerow.css('td')[2].get())
					row_data['Method'] = striptags(tablerow.css('td')[3].get())
					row_data['Reference'] = striptags(tablerow.css('td')[4].get())
					row_data['Comment'] = striptags(tablerow.css('td')[5].get())

					category_data.append(row_data)
			loader.add_value(self.subpage_data[subpage_id].replace('-', '_'), category_data)
			yield loader.load_item()
