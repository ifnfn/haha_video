function find(var, tag, key, value)
	-- check input:
	if type(var)~="table" then return end
	if type(tag)=="string" and #tag==0 then tag=nil end
	if type(key)~="string" or #key==0 then key=nil end
	if type(value)=="string" and #value==0 then value=nil end
	-- compare this table:
	if tag~=nil then
		if var[0]==tag and ( value == nil or var[key]==value ) then
			setmetatable(var,{__index=xml, __tostring=xml.str})
			return var
		end
	else
		if value == nil or var[key]==value then
			setmetatable(var,{__index=xml, __tostring=xml.str})
			return var
		end
	end
	-- recursively parse subtags:
	for k,v in ipairs(var) do
		if type(v)=="table" then
			local ret = find(v, tag, key,value)
			if ret ~= nil then return ret end
		end
	end
end

-- <?xml version="1.0" encoding="utf-8"?>
--<channel name="hoolo直播">
--	<drm drm="0"/>
--	<logos baseUrl="">
--		<item/>
--		<item/>
--		<item/>
--		<item/>
--	</logos>
--	<video baseUrl="" aspect="4:3">
--		<item/>
--		<item url="http://live2.hoolo.tv/channels/hoolo/hoolo/flv:sd/"/>
--		<item/>
--		<item url="http://live2.hoolo.tv/channels/hoolo/hoolo/flv:sd/"/>
--	</video>
--</channel>

function kola_main(url)
	local text = kola.wget(url)
	local ret_url = ''

	if text == nil then
		return ''
	end

	x = xml.eval(text)
	v= find(x, "video", "item")
	for a, b in pairs(v) do
		if b['url'] ~= nil then
			ret_url = b['url']
			break
		end
	end

	return ret_url
end
