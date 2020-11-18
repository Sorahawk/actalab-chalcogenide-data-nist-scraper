from scrapy.item import Item, Field
from scrapy.loader.processors import MapCompose, TakeFirst

class ChalcogenideData(Item):
	Chalcogenide_Name = Field(
		output_processor=TakeFirst()
		)
	Chalcogenide_Formula = Field()
	Thermo_Gas = Field()
	Thermo_Condensed = Field()
	Thermo_Phase = Field()
	Ion_Energetics = Field()
