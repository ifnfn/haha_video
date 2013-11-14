-- def GetURL():
-- haha = KolaClient()
-- url = 'http://api.cztv.com/api/getCDNByChannelId/%d?domain=api.cztv.com'
--
-- for i in range(100, 199):
-- 	u = url % i
-- 	text = haha.GetCacheUrl(u)
-- 	js = json.loads(text.decode())
--
-- 	datarates = js['result']['datarates']
-- 	if datarates != None:
-- 		k, v = list(datarates.items())[0]
-- 		timestamp = int(float(js['result']['timestamp']) / 1000) * 1000
-- 		u = 'http://%s/channels/%d/%s.flv/live?%d' % (v[0], i, k, timestamp)
-- 		print(u)

function kola_main(url)
	url = "http://api.cztv.com/api/getCDNByChannelId/102?domain=api.cztv.com"
	local text = kola.wget(url)
	local data_json = '{"result":{"datarates":{"500":["v2.cztv.com"]},"timestamp":"1.38442035065E+12","DRM":"false","WS":"false"}}'
	local data_obj = json.json_decode(data_json)
	return text
--	return kola.pcre("(window.google.*)", text)
end
