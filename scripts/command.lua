function update_command(param)
	print(param)
	local js = cjson.decode(param)

	for _,v in pairs(js.command) do
		if v.text then
			v.data = v.text
		else
			local text = kola.wget(v.source, false)
			if v.regular then
				local tmp = ''
				for _,r in pairs(v.regular) do
					for a in rex.gmatch (text, r) do
						tmp = tmp .. a .. '\n'
					end
				end
				text = string.sub(tmp, 1, -1)
			end
			v.data = text
		end
		kola.wpost(js.dest, cjson.encode(v))
	end

	return 'OK'
end
