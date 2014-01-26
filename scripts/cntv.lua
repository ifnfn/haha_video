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

function kola_main(vid, a)
	return string.format('http://hdshls.cntv.chinacache.net/cache/%s_/seg0/index.m3u8', a)
	--local url = string.format("http://vcbox.cntv.chinacache.net/cache/hds%s.f4m", vid)
	--local text = kola.wget(url)
	--if text == nil then
	--	url = string.format('http://vcbox.cntv.chinacache.net/cache/%s_/seg1/index.f4m', a)
	--	text = kola.wget(url)
	--end

	--if text == nil then
	--	return ''
	--end

	--local x = xml.eval(text)

	--local v= find(x, "manifest", "media")
	--for a, b in pairs(v) do
	--	--print(a,b)
	--	if b.streamId ~= nil then
	--		print(a, b.streamId, b.url, b.bitrate)
	--	end
	--end

	--return ''
end

function get_channel(vid)
	return ""
end
