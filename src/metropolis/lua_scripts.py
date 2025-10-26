COMPLETE_JOB_SCRIPT = """
local deps_count_hash = KEYS[1]
local ready_queue = KEYS[2]

local newly_ready_jobs = {}

for i, downstream_job_id in ipairs(ARGV) do
  local new_dep_count = redis.call('HINCRBY', deps_count_hash, downstream_job_id, -1)
  if new_dep_count == 0 then
    table.insert(newly_ready_jobs, downstream_job_id)
  end
end

if #newly_ready_jobs > 0 then
  redis.call('RPUSH', ready_queue, unpack(newly_ready_jobs))
end

return newly_ready_jobs
"""
