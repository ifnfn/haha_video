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

function kola_main(tv_id, channel_id)
	local url = string.format('http://ugc.sun-cam.com/api/tv_live_api.php?action=channel_prg_list&tv_id=%s', tv_id)
	local text = kola.wget(url)

	if text == nil then
		return ''
	end

	local x = xml.eval(text)
	local v = find(x, "videos")
	for a, b in pairs(v) do
		if b[0] == 'channel' then
			local ch_id = ''
			local v_url = ''
			local vv = find(b, 'channel')
			for aa, bb in pairs(vv) do
				if bb[0] == 'channel_id' then
					ch_id = bb[1]
				elseif bb[0] == 'mobile_url' then
					v_url = bb[1]
				end
			end

			if ch_id == channel_id then 
				--print(ch_id, v_url)
				return v_url
			end
		end
	end

	return ""
end

function get_channel(vid)
	return ""
end
