local metrics = redis.call('HGETALL', 'metropolis:metrics')

local result = {}


for i = 1, #metrics, 2 do
    local metric_name = metrics[i]
    local metric_value = metrics[i+1]
    local prom_key = "metropolis_" .. metric_name

   
    table.insert(result, prom_key)
    table.insert(result, metric_value)
end

return result