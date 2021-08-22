from src.api.edem_soveni import OTTProvider


class MockApi(OTTProvider):
	# hack to fix faling test
	NAME = "WowTV"

	def start(self):
		# skip extracting key from playlist
		pass
