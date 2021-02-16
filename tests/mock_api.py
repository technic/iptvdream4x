from src.api.edem_soveni import OTTProvider


class MockApi(OTTProvider):
	def start(self):
		# skip extracting key from playlist
		pass
