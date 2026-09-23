-- Adds meta["reading-time"] (for example "8 min read") to dated pages.
-- Only prose counts: code blocks, raw HTML and notebook cell outputs are skipped.
local WORDS_PER_MINUTE = 230

local function is_cell_output(el)
  return el.classes:find_if(function(c) return c:match("^cell%-output") end) ~= nil
end

function Pandoc(doc)
  if doc.meta.date == nil or doc.meta["reading-time"] ~= nil then
    return nil
  end
  local prose = pandoc.Pandoc(doc.blocks):walk({
    Div = function(el) if is_cell_output(el) then return {} end end,
    CodeBlock = function() return {} end,
    RawBlock = function() return {} end,
  })
  local words = 0
  prose:walk({
    Str = function() words = words + 1 end,
    Math = function() words = words + 1 end,
    Code = function() words = words + 1 end,
  })
  local minutes = math.max(1, math.ceil(words / WORDS_PER_MINUTE))
  doc.meta["reading-time"] = pandoc.MetaString(minutes .. " min read")
  return doc
end
